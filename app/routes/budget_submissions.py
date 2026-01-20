from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import BudgetSubmission
from app.schemas.budget import (
    BudgetSubmissionCreate,
    BudgetSubmissionOut,
    BudgetSubmissionUpdate,
)

router = APIRouter(prefix="/budget-submissions", tags=["budget-submissions"])


def _get_or_404(db: Session, submission_id: int) -> BudgetSubmission:
    submission = db.get(BudgetSubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Budget submission not found")
    return submission


@router.get("", response_model=list[BudgetSubmissionOut])
def list_submissions(
    skip: int = 0,
    limit: int = 100,
    assignment_id: int | None = None,
    student_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(BudgetSubmission)
    if assignment_id is not None:
        query = query.filter(BudgetSubmission.assignment_id == assignment_id)
    if student_id is not None:
        query = query.filter(BudgetSubmission.student_id == student_id)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=BudgetSubmissionOut, status_code=status.HTTP_201_CREATED)
def create_submission(payload: BudgetSubmissionCreate, db: Session = Depends(get_db)):
    submission = BudgetSubmission(**payload.model_dump())
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.get("/{submission_id}", response_model=BudgetSubmissionOut)
def get_submission(submission_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, submission_id)


@router.patch("/{submission_id}", response_model=BudgetSubmissionOut)
def update_submission(
    submission_id: int, payload: BudgetSubmissionUpdate, db: Session = Depends(get_db)
):
    submission = _get_or_404(db, submission_id)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(submission, key, value)
    db.commit()
    db.refresh(submission)
    return submission


@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_submission(submission_id: int, db: Session = Depends(get_db)):
    submission = _get_or_404(db, submission_id)
    db.delete(submission)
    db.commit()
    return None
