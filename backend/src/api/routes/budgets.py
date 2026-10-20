from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.deps import CurrentUserId
from src.db.models import Budget
from src.db.session import get_db
from src.ingest.categorize import CATEGORY_ENUM
from src.schemas.budget import BudgetCreate, BudgetOut
from src.services import analytics

router = APIRouter(prefix="/budgets", tags=["Budgets"])


def _current_month() -> str:
    now = datetime.utcnow()
    return f"{now.year:04d}-{now.month:02d}"


def _to_out(budget: Budget, spent_by_cat: dict[str, float]) -> dict:
    spent = spent_by_cat.get(budget.category, 0.0)
    return {
        "id": budget.id,
        "category": budget.category,
        "limit": budget.limit,
        "spent": round(spent, 2),
        "remaining": round(budget.limit - spent, 2),
    }


@router.get("", response_model=list[BudgetOut])
def list_budgets(user_id: CurrentUserId, db: Session = Depends(get_db)):
    budgets = db.execute(
        select(Budget).where(Budget.user_id == user_id).order_by(Budget.category)
    ).scalars().all()
    spent_by_cat = {
        row["category"]: row["amount"]
        for row in analytics.spending_by_category(db, user_id, _current_month())
    }
    return [_to_out(b, spent_by_cat) for b in budgets]


@router.post("", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
def create_budget(body: BudgetCreate, user_id: CurrentUserId, db: Session = Depends(get_db)):
    if body.category not in CATEGORY_ENUM:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown category: {body.category}")
    budget = Budget(user_id=user_id, category=body.category, limit=body.limit)
    db.add(budget)
    db.commit()
    db.refresh(budget)
    spent_by_cat = {
        row["category"]: row["amount"]
        for row in analytics.spending_by_category(db, user_id, _current_month())
    }
    return _to_out(budget, spent_by_cat)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(budget_id: int, user_id: CurrentUserId, db: Session = Depends(get_db)):
    budget = db.get(Budget, budget_id)
    if budget is None or budget.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Budget not found")
    db.delete(budget)
    db.commit()
