"""Pure-SQL analytics aggregates. LLM-free (ARCHITECTURE §3).

Every function takes an explicit `Session` so both the HTTP routes and the agent
tools call the identical code — the dashboard and the chat agent can never
disagree on a number. Every query filters `is_internal = false` so self-transfers
don't double-inflate gross income/expense (ARCHITECTURE §6.4), and every SUM is
coalesced to 0.0 so an empty DB returns zeros instead of NULL/500.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models import Transaction


def _month_bounds(month: str) -> tuple[datetime, datetime]:
    """'YYYY-MM' -> [first day of month, first day of next month)."""
    year, mon = (int(p) for p in month.split("-", 1))
    start = datetime(year, mon, 1)
    end = datetime(year + 1, 1, 1) if mon == 12 else datetime(year, mon + 1, 1)
    return start, end


def _month_str(dt: datetime) -> str:
    return f"{dt.year:04d}-{dt.month:02d}"


def _prev_month_start(dt: datetime) -> datetime:
    return datetime(dt.year - 1, 12, 1) if dt.month == 1 else datetime(dt.year, dt.month - 1, 1)


def monthly_summary(db: Session, user_id: int, month: str) -> dict:
    """income / expenses / net / savings_rate for one 'YYYY-MM' month."""
    start, end = _month_bounds(month)
    income_expr = func.coalesce(
        func.sum(Transaction.amount).filter(Transaction.amount > 0), 0.0
    )
    expense_expr = func.coalesce(
        func.sum(-Transaction.amount).filter(Transaction.amount < 0), 0.0
    )
    row = db.execute(
        select(income_expr, expense_expr).where(
            Transaction.user_id == user_id,
            Transaction.is_internal.is_(False),
            Transaction.date >= start,
            Transaction.date < end,
        )
    ).one()
    income = float(row[0] or 0.0)
    expenses = float(row[1] or 0.0)  # positive magnitude
    net = income - expenses
    savings_rate = (net / income * 100.0) if income > 0 else 0.0
    return {
        "month": month,
        "income": round(income, 2),
        "expenses": round(expenses, 2),
        "net": round(net, 2),
        "savings_rate": round(savings_rate, 1),
    }


def account_balance(db: Session, user_id: int) -> dict:
    """All-time net money in the account = SUM(amount) across every transaction.

    Amounts are signed (positive = income, negative = expense), so a plain sum is
    the running balance. Unlike the gross income/expense aggregates, this does NOT
    filter `is_internal`: a genuine self-transfer nets to zero and so can't inflate
    a net sum, while excluding internal rows corrupts the balance whenever the
    transfer-detection tags one leg of a transfer but not its counterpart (e.g. a
    one-sided account-funding inflow). Summing everything is the robust choice.
    """
    total = db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
            Transaction.user_id == user_id,
        )
    ).scalar()
    return {"total_balance": round(float(total or 0.0), 2)}


def spending_by_category(db: Session, user_id: int, month: str) -> list[dict]:
    """Expense totals grouped by category (positive magnitudes), largest first."""
    start, end = _month_bounds(month)
    # Reuse one coalesce object in SELECT and GROUP BY so Postgres sees them as
    # the same expression (separate func.coalesce() calls emit distinct params and
    # trigger "must appear in the GROUP BY clause").
    category_col = func.coalesce(Transaction.category, "Uncategorized")
    amount = func.sum(-Transaction.amount)
    rows = db.execute(
        select(
            category_col.label("category"),
            amount.label("amount"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.is_internal.is_(False),
            Transaction.amount < 0,  # expenses only
            Transaction.date >= start,
            Transaction.date < end,
        )
        .group_by(category_col)
        .order_by(amount.desc())
    ).all()
    return [{"category": r.category, "amount": round(float(r.amount or 0.0), 2)} for r in rows]


def spending_trend(db: Session, user_id: int, n_months: int) -> list[dict]:
    """income/expenses/net per month for the last `n_months`, oldest -> newest.

    Anchored on the latest transaction's month (or today if the DB is empty), so a
    trend always spans months that could contain data.
    """
    n_months = max(1, min(n_months, 24))
    latest = db.execute(
        select(func.max(Transaction.date)).where(
            Transaction.user_id == user_id,
            Transaction.is_internal.is_(False),
        )
    ).scalar()
    anchor = latest or datetime.utcnow()
    anchor = datetime(anchor.year, anchor.month, 1)

    cursor = anchor
    for _ in range(n_months - 1):
        cursor = _prev_month_start(cursor)
    # cursor is now the oldest month in the window

    items: list[dict] = []
    for _ in range(n_months):
        items.append(monthly_summary(db, user_id, _month_str(cursor)))
        # advance one month
        cursor = datetime(cursor.year + 1, 1, 1) if cursor.month == 12 else datetime(cursor.year, cursor.month + 1, 1)
    return [{"month": i["month"], "income": i["income"], "expenses": i["expenses"], "net": i["net"]} for i in items]
