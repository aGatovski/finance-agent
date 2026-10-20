from pydantic import BaseModel


class MonthlySummary(BaseModel):
    month: str
    income: float
    expenses: float
    net: float
    savings_rate: float


class CategoryAmount(BaseModel):
    category: str
    amount: float


class CategoryBreakdown(BaseModel):
    month: str
    items: list[CategoryAmount]


class TrendPoint(BaseModel):
    month: str
    income: float
    expenses: float
    net: float


class Trend(BaseModel):
    items: list[TrendPoint]


class Balance(BaseModel):
    total_balance: float
