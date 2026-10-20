from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.deps import CurrentUserId
from src.db.models import Goal
from src.db.session import get_db
from src.schemas.goal import GoalCreate, GoalOut, GoalUpdate

router = APIRouter(prefix="/goals", tags=["Goals"])


def _to_out(goal: Goal) -> dict:
    pct = (goal.current_amount / goal.target_amount * 100.0) if goal.target_amount > 0 else 0.0
    return {
        "id": goal.id,
        "name": goal.name,
        "target_amount": goal.target_amount,
        "current_amount": goal.current_amount,
        "deadline": goal.deadline,
        "progress_pct": round(min(pct, 100.0), 1),
    }


@router.get("", response_model=list[GoalOut])
def list_goals(user_id: CurrentUserId, db: Session = Depends(get_db)):
    goals = db.execute(
        select(Goal).where(Goal.user_id == user_id).order_by(Goal.id)
    ).scalars().all()
    return [_to_out(g) for g in goals]


@router.post("", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(body: GoalCreate, user_id: CurrentUserId, db: Session = Depends(get_db)):
    goal = Goal(
        user_id=user_id,
        name=body.name,
        target_amount=body.target_amount,
        current_amount=body.current_amount,
        deadline=body.deadline,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _to_out(goal)


@router.patch("/{goal_id}", response_model=GoalOut)
def update_goal(
    goal_id: int, body: GoalUpdate, user_id: CurrentUserId, db: Session = Depends(get_db)
):
    goal = db.get(Goal, goal_id)
    if goal is None or goal.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Goal not found")
    fields = body.model_dump(exclude_unset=True)
    if "target_amount" in fields and fields["target_amount"] is not None and fields["target_amount"] <= 0:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "target_amount must be greater than 0")
    for field, value in fields.items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return _to_out(goal)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: int, user_id: CurrentUserId, db: Session = Depends(get_db)):
    goal = db.get(Goal, goal_id)
    if goal is None or goal.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Goal not found")
    db.delete(goal)
    db.commit()
