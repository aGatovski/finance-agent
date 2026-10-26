from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
import re
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy import inspect, inspect, text
from src.rag.registry import get_retriever
from src.db.session import AgentSessionLocal, SessionLocal, agent_engine
from src.services import analytics
from src.config import settings


_kb_retriever = get_retriever("hybrid_rerank")

ALLOWED_TABLES = ["transactions", "budgets", "goals", "categories", "merchant_data"]
_FORBIDDEN = ("insert", "update", "delete", "drop", "alter",
              "create", "truncate", "grant", "revoke")

_model = GoogleGenerativeAIEmbeddings(
    model=settings.embedding_model,
    google_api_key=settings.gemini_api_key,
)


def _run_scoped(user_id: int, sql: str) -> list[dict]:
    """Open a read-only session, pin app.user_id so RLS filters to this user,
    run the SELECT, and roll back (nothing is ever written)."""
    with AgentSessionLocal() as session:
        session.execute(
            text("SELECT set_config('app.user_id', :uid, true)"),
            {"uid": str(user_id)},
        )
        result = session.execute(text(sql))
        rows = [dict(row) for row in result.mappings().all()]
        session.rollback()  # read-only: throw away the (empty) transaction
        return rows
    

def _guard(sql: str) -> str | None:
    """Return None if `sql` is a single read-only SELECT/WITH statement,
    otherwise a human-readable reason (which gets shown back to the model)."""
    cleaned = sql.strip().rstrip(";").strip()
    if not cleaned:
        return "Empty query."
    lowered = cleaned.lower()
    if ";" in cleaned:                       # one statement only
        return "Only a single statement is allowed (no ';'-chained queries)."
    if not (lowered.startswith("select") or lowered.startswith("with")):
        return "Only read-only SELECT queries are allowed."
    for kw in _FORBIDDEN:                     # belt-and-suspenders keyword block
        if re.search(rf"\b{kw}\b", lowered):
            return f"Forbidden keyword '{kw}' — only SELECT is allowed."
    return None



@tool
def list_tables() -> str:
    """Input is an empty string, output is a comma-separated list of tables in the database."""
    descriptions = {
        "transactions": "one row per transaction; amount is signed (negative = expense)",
        "budgets": "per-category monthly spending limits for the user",
        "goals": "savings goals with target and current amounts",
        "categories": "category names (some global, shared by all users)",
        "merchant_data": "global merchant → category lookup",
    }
    return "\n".join(f"{t}: {descriptions[t]}" for t in ALLOWED_TABLES)

@tool
def get_db_schema(table_names: str) -> str:
    """Input to this tool is a comma-separated list of tables, output is the schema and sample rows for those tables.
    Be sure that the tables actually exist by calling sql_db_list_tables first!
    Example Input: table1, table2, table3"""

    results  = []
    inspector =  inspect(agent_engine)

    for table in table_names.split(", "):
        table = table.strip()
        if table not in ALLOWED_TABLES:
            continue

        columns =  inspector.get_columns(table)
        results.append(f"TABLE {table}:")
        
        for col in columns:
            results.append(f"  {col['name']} ({col['type']})")

    return "\n".join(results)

@tool
def db_query_check(query: str) -> str:
    """Double-check a SQL query is a safe, read-only SELECT before running it.
    Returns 'OK', or the reason it was rejected. Call this before execute_db_query."""

    return _guard(query) or "OK"


@tool
def execute_db_query(query: str, config: RunnableConfig) -> list[dict] | str:
    """Run a read-only SELECT and return the matching rows.
    Only SELECT is allowed, and results are automatically scoped to the user.
    If unsure your SQL is valid, call check_query first."""

    problem = _guard(query)
    if problem:
        return problem

    user_id = config["configurable"]["user_id"]

    try:
        return _run_scoped(user_id, query)
    except Exception as e:
        return f"Query failed: {e}"



@tool
def search_knowledge_base(query: str) -> str:
    """Search the personal-finance knowledge base (budgeting, saving, debt,
    credit, taxes, investing, consumer protection) for guidance to answer a
    user's 'how/what/should I' question. Returns the most relevant passages.
    Use this for financial education/coaching questions — NOT for the user's own
    numbers (use the SQL tools for those)."""
    with SessionLocal() as db:
        chunks = _kb_retriever.retrieve(query, db, k=5)
    if not chunks:
        return "No relevant knowledge-base passages found."
    return "\n\n".join(
        f"[{c.source}] {c.title or ''}\n{c.content}".strip() for c in chunks
    )


TOOLS = [list_tables, get_db_schema, db_query_check, execute_db_query,search_knowledge_base]





