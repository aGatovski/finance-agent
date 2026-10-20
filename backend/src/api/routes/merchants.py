from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.api.deps import CurrentUserId
from src.db.models import MerchantData, Transaction
from src.db.session import get_db
from src.ingest.categorize import CATEGORY_ENUM
from src.schemas.merchant import MerchantOut, MerchantUpdate, MerchantUpdateResult

router = APIRouter(prefix="/merchants", tags=["Merchants"])


def _validate_category(category: str) -> None:
    if category not in CATEGORY_ENUM:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown category: {category}")


def _tx_count(db: Session, user_id: int, merchant_name: str) -> int:
    return db.execute(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.user_id == user_id, Transaction.merchant == merchant_name)
    ).scalar_one()


@router.get("", response_model=list[MerchantOut])
def list_merchants(
    user_id: CurrentUserId,
    search: str | None = None,
    category: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    # Per-merchant transaction counts for the current user (MerchantData is global).
    counts = (
        select(Transaction.merchant.label("merchant"), func.count().label("c"))
        .where(Transaction.user_id == user_id)
        .group_by(Transaction.merchant)
        .subquery()
    )
    stmt = (
        select(MerchantData, func.coalesce(counts.c.c, 0))
        .outerjoin(counts, counts.c.merchant == MerchantData.merchant_name)
        .order_by(MerchantData.merchant_name)
    )
    if search:
        stmt = stmt.where(MerchantData.merchant_name.ilike(f"%{search}%"))
    if category:
        stmt = stmt.where(MerchantData.category == category)
    rows = db.execute(stmt.limit(limit).offset(offset)).all()
    return [
        MerchantOut(
            id=md.id,
            merchant_name=md.merchant_name,
            category=md.category,
            is_internal=md.is_internal,
            tx_count=int(c or 0),
        )
        for md, c in rows
    ]


@router.patch("/{merchant_id}", response_model=MerchantUpdateResult)
def update_merchant(
    merchant_id: int,
    body: MerchantUpdate,
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
):
    """Change a learned merchant's category and/or internal flag. With
    apply_to_existing, also re-stamp this user's existing transactions for that
    merchant (category and/or is_internal, whichever changed)."""
    if body.category is not None:
        _validate_category(body.category)
    md = db.get(MerchantData, merchant_id)
    if md is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Merchant not found")

    if body.category is not None:
        md.category = body.category
    if body.is_internal is not None:
        md.is_internal = body.is_internal

    updated = 0
    if body.apply_to_existing and (body.category is not None or body.is_internal is not None):
        updates: dict = {}
        if body.category is not None:
            updates["category"] = body.category
            updates["category_src"] = "user"
        if body.is_internal is not None:
            updates["is_internal"] = body.is_internal
        updated = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id, Transaction.merchant == md.merchant_name)
            .update(updates, synchronize_session=False)
        )

    db.commit()
    db.refresh(md)
    return MerchantUpdateResult(
        merchant=MerchantOut(
            id=md.id,
            merchant_name=md.merchant_name,
            category=md.category,
            is_internal=md.is_internal,
            tx_count=_tx_count(db, user_id, md.merchant_name),
        ),
        updated_transactions=updated,
    )


@router.delete("/{merchant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_merchant(merchant_id: int, user_id: CurrentUserId, db: Session = Depends(get_db)):
    md = db.get(MerchantData, merchant_id)
    if md is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Merchant not found")
    db.delete(md)
    db.commit()
