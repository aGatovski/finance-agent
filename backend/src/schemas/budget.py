from pydantic import BaseModel


class BudgetCreate(BaseModel):
    category: str
    limit: float


class BudgetOut(BaseModel):
    id: int
    category: str
    limit: float
    spent: float
    remaining: float
