from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import BudgetLineItem
from app.schemas.budget import (
    BudgetLineItemCreate,
    BudgetLineItemOut,
    BudgetLineItemUpdate,
)

router = APIRouter(prefix="/budget-line-items", tags=["budget-line-items"])


def _get_or_404(db: Session, item_id: int) -> BudgetLineItem:
    item = db.get(BudgetLineItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Budget line item not found")
    return item


@router.get("", response_model=list[BudgetLineItemOut])
def list_line_items(
    skip: int = 0,
    limit: int = 100,
    submission_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(BudgetLineItem)
    if submission_id is not None:
        query = query.filter(BudgetLineItem.submission_id == submission_id)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=BudgetLineItemOut, status_code=status.HTTP_201_CREATED)
def create_line_item(payload: BudgetLineItemCreate, db: Session = Depends(get_db)):
    item = BudgetLineItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=BudgetLineItemOut)
def get_line_item(item_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, item_id)


@router.patch("/{item_id}", response_model=BudgetLineItemOut)
def update_line_item(
    item_id: int, payload: BudgetLineItemUpdate, db: Session = Depends(get_db)
):
    item = _get_or_404(db, item_id)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_line_item(item_id: int, db: Session = Depends(get_db)):
    item = _get_or_404(db, item_id)
    db.delete(item)
    db.commit()
    return None
