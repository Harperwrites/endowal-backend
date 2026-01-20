from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_roles
from app.models import Assignment, BudgetSubmission, User
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


def _get_assignment_or_404(db: Session, assignment_id: int) -> Assignment:
    assignment = db.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


def _ensure_assignment_access(
    db: Session, assignment_id: int, current_user: User
) -> Assignment:
    assignment = _get_assignment_or_404(db, assignment_id)
    if current_user.role == "teacher" and assignment.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return assignment


@router.get("", response_model=list[BudgetSubmissionOut])
def list_submissions(
    skip: int = 0,
    limit: int = 100,
    assignment_id: int | None = None,
    student_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(BudgetSubmission)
    if current_user.role == "student":
        if student_id is not None and student_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        student_id = current_user.id
    if current_user.role == "teacher":
        if assignment_id is not None:
            _ensure_assignment_access(db, assignment_id, current_user)
        else:
            query = query.join(
                Assignment, BudgetSubmission.assignment_id == Assignment.id
            ).filter(Assignment.created_by == current_user.id)
    if assignment_id is not None:
        query = query.filter(BudgetSubmission.assignment_id == assignment_id)
    if student_id is not None:
        query = query.filter(BudgetSubmission.student_id == student_id)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=BudgetSubmissionOut, status_code=status.HTTP_201_CREATED)
def create_submission(
    payload: BudgetSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = payload.model_dump()
    _ensure_assignment_access(db, data["assignment_id"], current_user)
    if current_user.role == "student":
        data["student_id"] = current_user.id
    submission = BudgetSubmission(**data)
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.get("/{submission_id}", response_model=BudgetSubmissionOut)
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = _get_or_404(db, submission_id)
    if current_user.role == "student" and submission.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "teacher":
        _ensure_assignment_access(db, submission.assignment_id, current_user)
    return submission


@router.patch("/{submission_id}", response_model=BudgetSubmissionOut)
def update_submission(
    submission_id: int,
    payload: BudgetSubmissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = _get_or_404(db, submission_id)
    if current_user.role == "student" and submission.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "teacher":
        _ensure_assignment_access(db, submission.assignment_id, current_user)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(submission, key, value)
    db.commit()
    db.refresh(submission)
    return submission


@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = _get_or_404(db, submission_id)
    if current_user.role == "student" and submission.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "teacher":
        _ensure_assignment_access(db, submission.assignment_id, current_user)
    db.delete(submission)
    db.commit()
    return None
