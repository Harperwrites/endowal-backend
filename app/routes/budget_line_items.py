from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models import Assignment, BudgetLineItem, BudgetSubmission, User
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


def _get_submission_or_404(db: Session, submission_id: int) -> BudgetSubmission:
    submission = db.get(BudgetSubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Budget submission not found")
    return submission


def _ensure_submission_access(
    db: Session, submission: BudgetSubmission, current_user: User
) -> None:
    if current_user.role == "student" and submission.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "teacher":
        assignment = db.get(Assignment, submission.assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        if assignment.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")


@router.get("", response_model=list[BudgetLineItemOut])
def list_line_items(
    skip: int = 0,
    limit: int = 100,
    submission_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(BudgetLineItem)
    if submission_id is None and current_user.role != "admin":
        raise HTTPException(status_code=400, detail="submission_id is required")
    if submission_id is not None:
        submission = _get_submission_or_404(db, submission_id)
        _ensure_submission_access(db, submission, current_user)
        query = query.filter(BudgetLineItem.submission_id == submission_id)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=BudgetLineItemOut, status_code=status.HTTP_201_CREATED)
def create_line_item(
    payload: BudgetLineItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = _get_submission_or_404(db, payload.submission_id)
    _ensure_submission_access(db, submission, current_user)
    item = BudgetLineItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=BudgetLineItemOut)
def get_line_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = _get_or_404(db, item_id)
    submission = _get_submission_or_404(db, item.submission_id)
    _ensure_submission_access(db, submission, current_user)
    return item


@router.patch("/{item_id}", response_model=BudgetLineItemOut)
def update_line_item(
    item_id: int,
    payload: BudgetLineItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = _get_or_404(db, item_id)
    submission = _get_submission_or_404(db, item.submission_id)
    _ensure_submission_access(db, submission, current_user)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_line_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = _get_or_404(db, item_id)
    submission = _get_submission_or_404(db, item.submission_id)
    _ensure_submission_access(db, submission, current_user)
    db.delete(item)
    db.commit()
    return None
