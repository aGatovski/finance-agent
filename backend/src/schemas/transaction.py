from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: datetime
    amount: float
    description: str | None
    merchant: str | None
    category: str | None
    category_src: str | None
    is_internal: bool
    type: str | None


class TransactionList(BaseModel):
    items: list[TransactionOut]
    total: int


class ImportResult(BaseModel):
    inserted: int
    skipped_internal: int
    categorized: int
    uncategorized: int
    format_cached: bool
    detected_mapping: dict


class CategoryUpdate(BaseModel):
    category: str


class TransactionCreate(BaseModel):
    date: datetime
    amount: float
    description: str | None = None
    merchant: str | None = None
    category: str | None = None
    type: str | None = None
    is_internal: bool = False


class TransactionUpdate(BaseModel):
    """Partial update — only provided fields are applied."""

    date: datetime | None = None
    amount: float | None = None
    description: str | None = None
    merchant: str | None = None
    category: str | None = None
    type: str | None = None
    is_internal: bool | None = None
