from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

agent_engine=create_engine(settings.agent_database_url, pool_pre_ping=True)
AgentSessionLocal  = sessionmaker(bind=agent_engine, autoflush=False, expire_on_commit=False)



class Base(DeclarativeBase):
    """Declarative base that every ORM model inherits from."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: hand out a DB session and always close it.

    Used as `db: Session = Depends(get_db)` in routes and other dependencies.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Dev helper: create every table from the models.

    Fine for local development. Switch to Alembic migrations once the schema
    starts changing (you already have alembic installed).
    """
    import src.db.models  # noqa: F401 — import so models register on Base
    
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text(
            "ALTER TABLE IF EXISTS transactions "
            "ADD COLUMN IF NOT EXISTS embedding vector(768)"
        ))
        conn.commit()
    Base.metadata.create_all(bind=engine)
