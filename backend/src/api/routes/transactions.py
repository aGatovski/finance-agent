from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.api.deps import CurrentUserId
from src.db.models import MerchantData, Transaction
from src.db.session import get_db
from src.ingest.categorize import CATEGORY_ENUM
from src.ingest.pipeline import run_import
from src.schemas.transaction import (
    ImportResult,
    TransactionCreate,
    TransactionList,
    TransactionOut,
    TransactionUpdate,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def _validate_category(category: str) -> None:
    if category not in CATEGORY_ENUM:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown category: {category}")


@router.get("", response_model=TransactionList)
def list_transactions(
    user_id: CurrentUserId,
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    category: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    filters = [Transaction.user_id == user_id]
    if month:
        year, mon = (int(p) for p in month.split("-", 1))
        start = datetime(year, mon, 1)
        end = datetime(year + 1, 1, 1) if mon == 12 else datetime(year, mon + 1, 1)
        filters += [Transaction.date >= start, Transaction.date < end]
    if category:
        filters.append(Transaction.category == category)

    total = db.execute(
        select(func.count()).select_from(Transaction).where(*filters)
    ).scalar_one()
    items = db.execute(
        select(Transaction)
        .where(*filters)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .limit(limit)
        .offset(offset)
    ).scalars().all()
    return {"items": items, "total": total}


@router.post("/import", response_model=ImportResult)
async def import_csv(
    user_id: CurrentUserId,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    if not content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file")
    try:
        return run_import(content, user_id, db)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - surface parse/LLM failures cleanly
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Import failed: {exc}")


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    body: TransactionCreate,
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
):
    """Manually add a single transaction (not via CSV)."""
    if body.category is not None:
        _validate_category(body.category)
    tx = Transaction(
        user_id=user_id,
        date=body.date,
        amount=body.amount,
        description=body.description,
        merchant=body.merchant,
        category=body.category or "Uncategorized",
        category_src="user",
        type=body.type,
        is_internal=body.is_internal,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.patch("/{tx_id}", response_model=TransactionOut)
def update_transaction(
    tx_id: int,
    body: TransactionUpdate,
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
    apply_to_merchant: bool = Query(default=False),
):
    """Partial update — only provided fields change. Changing the category also upserts
    the MerchantData lookup so the fix sticks on the next import (ARCHITECTURE §6.3).
    With apply_to_merchant, also re-stamp this user's other transactions for the same
    merchant. The inline category dropdown uses this with just `{category}`."""
    fields = body.model_dump(exclude_unset=True)
    tx = db.get(Transaction, tx_id)
    if tx is None or tx.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")

    if "category" in fields and fields["category"] is not None:
        _validate_category(fields["category"])

    for key, value in fields.items():
        setattr(tx, key, value)

    if "category" in fields and fields["category"] is not None:
        tx.category_src = "user"
        if tx.merchant:
            existing = db.execute(
                select(MerchantData).where(MerchantData.merchant_name == tx.merchant)
            ).scalar_one_or_none()
            if existing:
                existing.category = fields["category"]
            else:
                db.add(MerchantData(merchant_name=tx.merchant, category=fields["category"]))
            if apply_to_merchant:
                db.query(Transaction).filter(
                    Transaction.user_id == user_id,
                    Transaction.merchant == tx.merchant,
                    Transaction.id != tx.id,
                ).update(
                    {"category": fields["category"], "category_src": "user"},
                    synchronize_session=False,
                )

    db.commit()
    db.refresh(tx)
    return tx


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(tx_id: int, user_id: CurrentUserId, db: Session = Depends(get_db)):
    tx = db.get(Transaction, tx_id)
    if tx is None or tx.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    db.delete(tx)
    db.commit()
