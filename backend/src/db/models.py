from datetime import date, datetime
from sqlalchemy import Integer, String, Float, DateTime, Date, Boolean, ForeignKey, Text
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column
from src.db.session import Base
from sqlalchemy.dialects.postgresql import TSVECTOR


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    bio: Mapped[str | None] = mapped_column(String, nullable=True)


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[str | None] = mapped_column(String, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime)
    amount: Mapped[float] = mapped_column(Float)          # negative = expense
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    merchant: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    category_src: Mapped[str | None] = mapped_column(String, nullable=True)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)


class MerchantData(Base):
    """Merchant→category lookup / self-learning table.

    The categorizer's deterministic lookup hits this first; novel merchants are
    resolved by a batched LLM call and written back here, so the next import is a
    free lookup.
    """

    __tablename__ = "merchant_data"
    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_name: Mapped[str] = mapped_column(String, unique=True, index=True)
    category: Mapped[str] = mapped_column(String)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Budget(Base):
    __tablename__ = "budgets"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String)
    limit: Mapped[float] = mapped_column(Float)


class Goal(Base):
    __tablename__ = "goals"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String)
    target_amount: Mapped[float] = mapped_column(Float)
    current_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    # NULL user_id = a global/default category shared by all users.
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String)


class KnowledgeChunk(Base):
    __tablename__= "knowledge_chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String, index=True)          # filename, for citations
    title: Mapped[str | None] = mapped_column(String, nullable=True) # human-readable doc title
    chunk_index: Mapped[int] = mapped_column(Integer)               # order within the source doc
    content: Mapped[str] = mapped_column(Text)
    content_tsv: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)  # Postgres full-text vector for BM25/hybrid
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)
    