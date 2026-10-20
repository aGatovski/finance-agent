from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.rag.backfill import backfill_embeddings
from src.config import settings
from src.agent.graph import build_agent_graph
from src.db.session import SessionLocal, init_db
from src.api.deps import DEV_USER_ID
from src.db.models import User
from langgraph.checkpoint.memory import InMemorySaver
from src.api.routes import chat, analytics, transactions, budgets, goals, categories, merchants


def ensure_dev_user() -> None:
    """Guarantee the DEV_USER_ID row exists so FK-bound inserts (transactions,
    budgets, goals) succeed before real auth is wired. Not sample data — just the
    identity the dev seam runs as."""
    with SessionLocal() as db:
        if db.get(User, DEV_USER_ID) is None:
            db.add(
                User(
                    id=DEV_USER_ID,
                    email="dev@local",
                    hashed_password="!",  # unusable; dev identity has no login
                    full_name="Dev User",
                )
            )
            db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # create tables if missing (idempotent; needs Postgres up — see §8)
    ensure_dev_user()
   
    # 
    
    saver = InMemorySaver()
    # async with AsyncPostgresSaver.from_conn_string(settings.DATABASE_URL) as saver:
    #    await saver.setup()  # creates checkpoint tables on first run
    #    app.state.agent = build_agent_graph(saver)
    app.state.agent = build_agent_graph(saver)
    yield


app = FastAPI(
    title="Finanse Assistant",
    description="Personal budgeting and financial coaching assistant",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat.router)
app.include_router(analytics.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(goals.router)
app.include_router(categories.router)
app.include_router(merchants.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "API is running"}

# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

