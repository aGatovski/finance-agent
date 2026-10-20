from sqlalchemy import select
from sqlalchemy.orm import Session
from src.db.models import Transaction
from src.rag.transaction_embedding import embed_texts, format_transaction_for_embedding

_BATCH = 100

def backfill_embeddings(db: Session) -> int:
    """Embed all Transaction rows with embedding IS NULL. Returns count updated."""
    stmt = select(Transaction).where(
        Transaction.embedding.is_(None),
        Transaction.is_internal.is_(False),
    )
    rows = db.execute(stmt).scalars().all()
    if not rows:
        return 0

    updated = 0
    for i in range(0, len(rows), _BATCH):
        batch = rows[i : i + _BATCH]
        texts = [format_transaction_for_embedding(tx) for tx in batch]
        vectors = embed_texts(texts)
        for tx, vec in zip(batch, vectors):
            tx.embedding = vec
        db.flush()
        updated += len(batch)

    db.commit()
    return updated