from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from src.db.session import SessionLocal
from src.services import analytics


@tool
def get_monthly_summary(month: str, config: RunnableConfig) -> dict:
    """Return exact income, expenses, net, and savings rate for a month.
    `month` is 'YYYY-MM'. Use this for any question about totals or savings.
    These numbers are authoritative — never recompute or estimate them."""
    user_id = config["configurable"]["user_id"]
    with SessionLocal() as db:  # tools aren't FastAPI deps — manage the session here
        return analytics.monthly_summary(db, user_id, month)


@tool
def get_spending_by_category(month: str, config: RunnableConfig) -> dict:
    """Return expense totals grouped by category for a 'YYYY-MM' month."""
    user_id = config["configurable"]["user_id"]
    with SessionLocal() as db:
        return {"month": month, "by_category": analytics.spending_by_category(db, user_id, month)}

from src.rag.retriever import search_transactions as _rag_search


@tool
def search_transactions(query: str, config: RunnableConfig) -> list[dict]:
    """Find transactions semantically related to a natural-language query.
    Use for questions like 'when did I last spend on X', 'find all Y payments',
    or 'show me anything related to Z'. Returns up to 10 matching transactions
    with date, merchant, description, amount, and category."""
    user_id = config["configurable"]["user_id"]
    with SessionLocal() as db:
        return _rag_search(query=query, user_id=user_id, db=db)

TOOLS = [get_monthly_summary, get_spending_by_category, search_transactions]




