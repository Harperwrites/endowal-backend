from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_roles
from app.models import Assignment, User
from app.schemas.assignment import AssignmentCreate, AssignmentOut, AssignmentUpdate

router = APIRouter(prefix="/assignments", tags=["assignments"])


def _get_or_404(db: Session, assignment_id: int) -> Assignment:
    assignment = db.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.get("", response_model=list[AssignmentOut])
def list_assignments(
    skip: int = 0,
    limit: int = 100,
    classroom_id: int | None = None,
    created_by: int | None = None,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Assignment)
    if classroom_id is not None:
        query = query.filter(Assignment.classroom_id == classroom_id)
    if created_by is not None:
        query = query.filter(Assignment.created_by == created_by)
    if status_filter:
        query = query.filter(Assignment.status == status_filter)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
def create_assignment(
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    data = payload.model_dump()
    if current_user.role == "teacher":
        data["created_by"] = current_user.id
    assignment = Assignment(**data)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/{assignment_id}", response_model=AssignmentOut)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return _get_or_404(db, assignment_id)


@router.patch("/{assignment_id}", response_model=AssignmentOut)
def update_assignment(
    assignment_id: int,
    payload: AssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    assignment = _get_or_404(db, assignment_id)
    if current_user.role == "teacher" and assignment.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(assignment, key, value)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    assignment = _get_or_404(db, assignment_id)
    if current_user.role == "teacher" and assignment.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(assignment)
    db.commit()
    return None
