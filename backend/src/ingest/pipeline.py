from __future__ import annotations
import io
import pandas as pd
from sqlalchemy.orm import Session
from src.db.models import Transaction
from src.ingest.categorize import categorize_rows
from src.ingest.mapper import infer_mapping
from src.ingest.normalize import normalize
from src.ingest.transfers import flag_internal

from src.rag.transaction_embedding import embed_texts, format_transaction_for_embedding


def run_import(file_bytes: bytes, user_id: int, db: Session) -> dict:
    df = pd.read_csv(io.BytesIO(file_bytes))
    df = df.dropna(how="all")
    columns = [str(c) for c in df.columns]

    sample_rows = df.head(5).to_dict(orient="records")
    mapping, from_cache = infer_mapping(columns, sample_rows)

    rows = normalize(df, mapping)
    skipped_internal = flag_internal(rows)
    categorize_rows(rows, db)

    embeddable = [r for r in rows if not r.get("is_internal")]
    vectors = embed_texts([format_transaction_for_embedding(r) for r in embeddable])
    vec_map = {id(r): vec for r, vec in zip(embeddable, vectors)}

    for r in rows:
        db.add(
            Transaction(
                user_id=user_id,
                type=r.get("type"),
                date=r["date"],
                amount=r["amount"],
                description=r.get("description"),
                merchant=r.get("merchant"),
                category=r.get("category"),
                category_src=r.get("category_src"),
                is_internal=r.get("is_internal", False),
                embedding=vec_map.get(id(r)),
            )
        )
    db.commit()

    categorized = sum(
        1 for r in rows if not r.get("is_internal") and r.get("category") != "Uncategorized"
    )
    uncategorized = sum(1 for r in rows if r.get("category") == "Uncategorized")

    return {
        "inserted": len(rows),
        "skipped_internal": skipped_internal,
        "categorized": categorized,
        "uncategorized": uncategorized,
        "format_cached": from_cache,
        "detected_mapping": mapping.model_dump(),
    }
