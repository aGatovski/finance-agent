from sqlalchemy import select
from sqlalchemy.orm import Session
from src.db.models import Transaction
from src.rag.transaction_embedding import embed_query

def search_transactions(
    query: str,
    user_id: int,
    db: Session,
    k: int = 10,
) -> list[dict]:
    """Return up to k transactions most semantically similar to `query`."""
    vec = embed_query(query)
    stmt = (
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.is_internal.is_(False),
            Transaction.embedding.is_not(None),
        )
        .order_by(Transaction.embedding.cosine_distance(vec))
        .limit(k)
    )
    rows = db.execute(stmt).scalars().all()
    return [
        {
            "date": tx.date.date().isoformat(),
            "merchant": tx.merchant,
            "description": tx.description,
            "amount": tx.amount,
            "category": tx.category,
        }
        for tx in rows
    ]
