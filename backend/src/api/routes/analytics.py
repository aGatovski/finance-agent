from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.deps import CurrentUserId
from src.db.session import get_db
from src.schemas.analytics import Balance, CategoryBreakdown, MonthlySummary, Trend
from src.services import analytics

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _default_month() -> str:
    now = datetime.utcnow()
    return f"{now.year:04d}-{now.month:02d}"


@router.get("/summary", response_model=MonthlySummary)
def summary(
    user_id: CurrentUserId,
    month: str = Query(default_factory=_default_month, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
):
    return analytics.monthly_summary(db, user_id, month)


@router.get("/by-category", response_model=CategoryBreakdown)
def by_category(
    user_id: CurrentUserId,
    month: str = Query(default_factory=_default_month, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
):
    return {"month": month, "items": analytics.spending_by_category(db, user_id, month)}


@router.get("/trend", response_model=Trend)
def trend(
    user_id: CurrentUserId,
    months: int = Query(default=6, ge=1, le=24),
    db: Session = Depends(get_db),
):
    return {"items": analytics.spending_trend(db, user_id, months)}


@router.get("/balance", response_model=Balance)
def balance(user_id: CurrentUserId, db: Session = Depends(get_db)):
    return analytics.account_balance(db, user_id)
