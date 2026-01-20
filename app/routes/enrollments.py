from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Enrollment
from app.schemas.enrollment import EnrollmentCreate, EnrollmentOut, EnrollmentUpdate

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


def _get_or_404(db: Session, enrollment_id: int) -> Enrollment:
    enrollment = db.get(Enrollment, enrollment_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return enrollment


@router.get("", response_model=list[EnrollmentOut])
def list_enrollments(
    skip: int = 0,
    limit: int = 100,
    classroom_id: int | None = None,
    student_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Enrollment)
    if classroom_id is not None:
        query = query.filter(Enrollment.classroom_id == classroom_id)
    if student_id is not None:
        query = query.filter(Enrollment.student_id == student_id)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
def create_enrollment(payload: EnrollmentCreate, db: Session = Depends(get_db)):
    enrollment = Enrollment(**payload.model_dump())
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.get("/{enrollment_id}", response_model=EnrollmentOut)
def get_enrollment(enrollment_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, enrollment_id)


@router.patch("/{enrollment_id}", response_model=EnrollmentOut)
def update_enrollment(
    enrollment_id: int, payload: EnrollmentUpdate, db: Session = Depends(get_db)
):
    enrollment = _get_or_404(db, enrollment_id)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(enrollment, key, value)
    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_enrollment(enrollment_id: int, db: Session = Depends(get_db)):
    enrollment = _get_or_404(db, enrollment_id)
    db.delete(enrollment)
    db.commit()
    return None
