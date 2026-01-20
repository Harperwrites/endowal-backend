from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Classroom
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
):
    query = db.query(Classroom)
    if teacher_id is not None:
        query = query.filter(Classroom.teacher_id == teacher_id)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=ClassroomOut, status_code=status.HTTP_201_CREATED)
def create_classroom(payload: ClassroomCreate, db: Session = Depends(get_db)):
    classroom = Classroom(**payload.model_dump())
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


@router.get("/{classroom_id}", response_model=ClassroomOut)
def get_classroom(classroom_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, classroom_id)


@router.patch("/{classroom_id}", response_model=ClassroomOut)
def update_classroom(
    classroom_id: int, payload: ClassroomUpdate, db: Session = Depends(get_db)
):
    classroom = _get_or_404(db, classroom_id)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(classroom, key, value)
    db.commit()
    db.refresh(classroom)
    return classroom


@router.delete("/{classroom_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_classroom(classroom_id: int, db: Session = Depends(get_db)):
    classroom = _get_or_404(db, classroom_id)
    db.delete(classroom)
    db.commit()
    return None
