from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_roles
from app.models import Classroom, User
from app.schemas.classroom import ClassroomCreate, ClassroomOut, ClassroomUpdate

router = APIRouter(prefix="/classrooms", tags=["classrooms"])


def _get_or_404(db: Session, classroom_id: int) -> Classroom:
    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    return classroom


@router.get("", response_model=list[ClassroomOut])
def list_classrooms(
    skip: int = 0,
    limit: int = 100,
    teacher_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Classroom)
    if teacher_id is not None:
        query = query.filter(Classroom.teacher_id == teacher_id)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=ClassroomOut, status_code=status.HTTP_201_CREATED)
def create_classroom(
    payload: ClassroomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    data = payload.model_dump()
    if current_user.role == "teacher":
        data["teacher_id"] = current_user.id
    classroom = Classroom(**data)
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


@router.get("/{classroom_id}", response_model=ClassroomOut)
def get_classroom(
    classroom_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return _get_or_404(db, classroom_id)


@router.patch("/{classroom_id}", response_model=ClassroomOut)
def update_classroom(
    classroom_id: int,
    payload: ClassroomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    classroom = _get_or_404(db, classroom_id)
    if current_user.role == "teacher" and classroom.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(classroom, key, value)
    db.commit()
    db.refresh(classroom)
    return classroom


@router.delete("/{classroom_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_classroom(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    classroom = _get_or_404(db, classroom_id)
    if current_user.role == "teacher" and classroom.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(classroom)
    db.commit()
    return None
