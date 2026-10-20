from datetime import date

from pydantic import BaseModel


class GoalCreate(BaseModel):
    name: str
    target_amount: float
    current_amount: float = 0.0
    deadline: date | None = None


class GoalUpdate(BaseModel):
    name: str | None = None
    target_amount: float | None = None
    current_amount: float | None = None
    deadline: date | None = None


class GoalOut(BaseModel):
    id: int
    name: str
    target_amount: float
    current_amount: float
    deadline: date | None
    progress_pct: float
