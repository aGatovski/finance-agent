from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import settings
from src.db.models import MerchantData

CATEGORY_ENUM = [
    "Groceries&Provisions",
    "Rent",
    "Dining",
    "Transport",
    "Subscriptions&Fees",
    "Utilities",
    "Shopping",
    "Health",
    "Entertainment",
    "Income",
    "Transfer",
    "Uncategorized",
]


class _MerchantCategory(BaseModel):
    merchant: str
    category: str = Field(description=f"One of: {', '.join(CATEGORY_ENUM)}")


class _Batch(BaseModel):
    assignments: list[_MerchantCategory]


_BATCH_SIZE = 40  # merchants per LLM call


def _llm_categorize(merchants: list[str]) -> dict[str, str]:
    if not merchants:
        return {}
    model = ChatGoogleGenerativeAI(
        model=settings.gemini_model, temperature=0, google_api_key=settings.gemini_api_key
    ).with_structured_output(_Batch)
    valid = set(CATEGORY_ENUM)
    result: dict[str, str] = {}
    # Chunk: one giant call (hundreds of merchants) overflows the structured-output
    # response and silently yields nothing. Batches of ~40 stay reliable.
    for i in range(0, len(merchants), _BATCH_SIZE):
        chunk = merchants[i : i + _BATCH_SIZE]
        prompt = (
            "Assign each merchant to exactly one category from this fixed list:\n"
            f"{', '.join(CATEGORY_ENUM)}\n\n"
            "Merchants:\n" + "\n".join(f"- {m}" for m in chunk)
        )
        try:
            batch: _Batch = model.invoke(prompt)
        except Exception:
            continue  # a failed chunk leaves its merchants Uncategorized; others still resolve
        for a in batch.assignments:
            if a.category in valid:
                result[a.merchant] = a.category
    return result


def categorize_rows(rows: list[dict], db: Session) -> None:
    """Set `category` and `category_src` on each non-internal row, in place.

    Writes newly-resolved merchants back to MerchantData for future free lookups.
    """
    # Look up every merchant once — we need both the learned category AND the
    # learned is_internal flag (e.g. DSK→Revolut self-transfers).
    all_merchants = {r["merchant"] for r in rows if r.get("merchant")}
    known: dict[str, MerchantData] = {}
    if all_merchants:
        for md in (
            db.execute(select(MerchantData).where(MerchantData.merchant_name.in_(all_merchants)))
            .scalars()
            .all()
        ):
            known[md.merchant_name] = md

    # Apply learned internal flags on top of flag_internal's type/pair rules.
    for r in rows:
        m = r.get("merchant")
        if m and m in known and known[m].is_internal:
            r["is_internal"] = True

    resolved: dict[str, tuple[str, str]] = {}  # merchant -> (category, source)

    # 1) Exact lookup — free, deterministic, covers recurring (non-internal) merchants.
    pending = {r["merchant"] for r in rows if not r.get("is_internal") and r.get("merchant")}
    for m in pending:
        md = known.get(m)
        if md is not None:
            resolved[m] = (md.category, "lookup")

    # 2) Batched LLM for the unknown tail, then write back.
    unknown = sorted(pending - set(resolved))
    if unknown:
        llm_result = _llm_categorize(unknown)
        for merchant, category in llm_result.items():
            resolved[merchant] = (category, "llm")
            db.add(MerchantData(merchant_name=merchant, category=category))
        if llm_result:
            db.flush()  # persist write-backs within the import transaction

    # 3) Stamp every row.
    for r in rows:
        if r.get("is_internal"):
            r["category"] = "Transfer"
            r["category_src"] = "lookup"
            continue
        merchant = r.get("merchant")
        if merchant and merchant in resolved:
            r["category"], r["category_src"] = resolved[merchant]
        else:
            r["category"], r["category_src"] = "Uncategorized", "fallback"
