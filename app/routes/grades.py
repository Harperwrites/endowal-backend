from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.session import get_db
from app.deps import get_current_user, require_roles
from app.models import Assignment, Classroom, Enrollment, User
from app.models.grade import Grade
from app.schemas.grade import GradeInput

router = APIRouter(prefix="/grades", tags=["grades"])


def classroom_access(db, classroom_id, user):
    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(404, "Classroom not found")
    if user.role == "teacher" and classroom.teacher_id != user.id:
        raise HTTPException(403, "Not authorized for this classroom")
    return classroom


@router.get("/roster")
def roster(classroom_id: int, db: Session = Depends(get_db),
           user: User = Depends(require_roles("teacher", "admin"))):
    classroom_access(db, classroom_id, user)
    students = db.query(User).join(Enrollment, Enrollment.student_id == User.id).filter(
        Enrollment.classroom_id == classroom_id, Enrollment.status == "active",
        User.role == "student", User.is_active.is_(True),
    ).order_by(User.name, User.id).all()
    assignments = db.query(Assignment).filter(Assignment.classroom_id == classroom_id).order_by(Assignment.id).all()
    return {"students": [{"id": s.id, "name": s.name or s.email} for s in students],
            "assignments": [{"id": a.id, "title": a.title} for a in assignments]}


@router.get("")
def list_grades(classroom_id: int | None = None, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    query = db.query(Grade, Assignment, Classroom, User).join(
        Assignment, Assignment.id == Grade.assignment_id
    ).join(Classroom, Classroom.id == Assignment.classroom_id).join(User, User.id == Grade.student_id)
    if user.role == "student":
        query = query.filter(Grade.student_id == user.id)
    elif user.role == "teacher":
        query = query.filter(Classroom.teacher_id == user.id)
    elif user.role != "admin":
        raise HTTPException(403, "Not authorized")
    if classroom_id is not None:
        query = query.filter(Classroom.id == classroom_id)
    return [{"id": g.id, "assignment_id": a.id, "assignment_title": a.title,
             "classroom_id": c.id, "classroom_name": c.name,
             "student_id": s.id, "student_name": s.name or s.email,
             "points_earned": str(g.points_earned), "points_possible": str(g.points_possible),
             "feedback": g.feedback, "updated_at": g.updated_at.isoformat()}
            for g, a, c, s in query.order_by(Grade.updated_at.desc(), Grade.id.desc()).all()]


@router.put("")
def save_grade(payload: GradeInput, db: Session = Depends(get_db),
               user: User = Depends(require_roles("teacher", "admin"))):
    assignment = db.get(Assignment, payload.assignment_id)
    if assignment is None:
        raise HTTPException(404, "Assignment not found")
    classroom_access(db, assignment.classroom_id, user)
    student = db.get(User, payload.student_id)
    enrolled = db.query(Enrollment).filter(
        Enrollment.classroom_id == assignment.classroom_id,
        Enrollment.student_id == payload.student_id, Enrollment.status == "active",
    ).first()
    if not student or student.role != "student" or not student.is_active or not enrolled:
        raise HTTPException(400, "Select an active student enrolled in this classroom")
    grade = db.query(Grade).filter(Grade.assignment_id == assignment.id, Grade.student_id == student.id).first()
    if grade is None:
        grade = Grade(assignment_id=assignment.id, student_id=student.id)
        db.add(grade)
    grade.points_earned = payload.points_earned
    grade.points_possible = payload.points_possible
    grade.feedback = payload.feedback.strip() if payload.feedback else None
    grade.graded_by = user.id
    grade.updated_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "This grade was updated at the same time. Refresh and try again.")
    db.refresh(grade)
    return {"id": grade.id, "status": "saved"}
