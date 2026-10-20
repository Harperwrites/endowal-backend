from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.session import get_db
from app.deps import get_current_user, require_roles
from app.models import Assignment, Classroom, Enrollment, User, Grade, StudentWallet
from app.models.workflow import AssignmentSubmission, now

router = APIRouter(prefix="/learning", tags=["learning"])

def access(db, classroom_id, user):
    room = db.get(Classroom, classroom_id)
    if not room: raise HTTPException(404, "Classroom not found")
    if user.role == "teacher" and room.teacher_id == user.id: return room
    if user.role == "admin": return room
    if user.role == "student" and db.query(Enrollment).filter_by(classroom_id=room.id, student_id=user.id, status="active").first(): return room
    raise HTTPException(403, "Not authorized for this classroom")

def timestamp(value):
    return value.replace(tzinfo=timezone.utc).isoformat() if value.tzinfo is None else value.isoformat()

def submission_json(s):
    return {"id":s.id,"student_id":s.student_id,"assignment_id":s.assignment_id,"content":s.content,"submitted_at":timestamp(s.submitted_at)}

@router.get("/classrooms")
def classrooms(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Classroom)
    if user.role == "teacher": query = query.filter(Classroom.teacher_id == user.id)
    elif user.role == "student": query = query.join(Enrollment, Enrollment.classroom_id == Classroom.id).filter(Enrollment.student_id == user.id, Enrollment.status == "active")
    elif user.role != "admin": raise HTTPException(403, "Not authorized")
    return [{"id":c.id,"name":c.name,"school_name":c.school_name,"grade_level":c.grade_level,
             "teacher_name":db.get(User,c.teacher_id).name,
             "student_count":db.query(Enrollment).filter_by(classroom_id=c.id,status="active").count()} for c in query.order_by(Classroom.id).all()]

@router.get("/classrooms/{classroom_id}")
def classroom_detail(classroom_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    room = access(db,classroom_id,user)
    assignments = db.query(Assignment).filter_by(classroom_id=room.id)
    if user.role == "student": assignments = assignments.filter(Assignment.status != "draft")
    work=[]
    for a in assignments.order_by(Assignment.due_date, Assignment.id).all():
        query=db.query(AssignmentSubmission).filter_by(assignment_id=a.id)
        if user.role == "student": query=query.filter_by(student_id=user.id)
        submissions=query.order_by(AssignmentSubmission.id).all()
        work.append({"id":a.id,"title":a.title,"description":a.description,"due_date":str(a.due_date) if a.due_date else None,"status":a.status,"submissions":[submission_json(s) for s in submissions]})
    roster=[]
    if user.role != "student":
        students=db.query(User).join(Enrollment,Enrollment.student_id==User.id).filter(Enrollment.classroom_id==room.id,Enrollment.status=="active",User.role=="student").order_by(User.name).all()
        roster=[{"id":s.id,"name":s.name} for s in students]
    return {"id":room.id,"name":room.name,"assignments":work,"students":roster}

class TurnIn(BaseModel):
    content: str = Field(min_length=1,max_length=20000)
    @field_validator("content")
    @classmethod
    def nonempty(cls,value):
        if not value.strip(): raise ValueError("Add your assignment response")
        return value.strip()

@router.put("/assignments/{assignment_id}/submission")
def turn_in(assignment_id: int, payload: TurnIn, db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    assignment=db.get(Assignment,assignment_id)
    if not assignment: raise HTTPException(404,"Assignment not found")
    access(db,assignment.classroom_id,user)
    if assignment.status not in ("active","published"): raise HTTPException(400,"This assignment is not open for submissions")
    submission=db.query(AssignmentSubmission).filter_by(assignment_id=assignment.id,student_id=user.id).first()
    if not submission:
        submission=AssignmentSubmission(assignment_id=assignment.id,student_id=user.id)
        db.add(submission)
    submission.content=payload.content; submission.submitted_at=now()
    try: db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409,"Submission changed. Refresh and try again.")
    db.refresh(submission)
    return submission_json(submission)

@router.get("/classrooms/{classroom_id}/students/{student_id}")
def student_dashboard(classroom_id: int, student_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("teacher","admin"))):
    room=access(db,classroom_id,user)
    enrolled=db.query(Enrollment).filter_by(classroom_id=room.id,student_id=student_id,status="active").first()
    student=db.get(User,student_id)
    if not enrolled or not student or student.role!="student": raise HTTPException(404,"Student not enrolled in this classroom")
    wallets=db.query(StudentWallet).filter_by(classroom_id=room.id,student_id=student_id).all()
    grades=db.query(Grade,Assignment).join(Assignment,Assignment.id==Grade.assignment_id).filter(Assignment.classroom_id==room.id,Grade.student_id==student_id).all()
    submissions=db.query(AssignmentSubmission,Assignment).join(Assignment,Assignment.id==AssignmentSubmission.assignment_id).filter(Assignment.classroom_id==room.id,AssignmentSubmission.student_id==student_id).all()
    return {"id":student.id,"name":student.name,"classroom_name":room.name,
        "wallets":[{"id":w.id,"balance":str(w.balance)} for w in wallets],
        "grades":[{"assignment_title":a.title,"points_earned":str(g.points_earned),"points_possible":str(g.points_possible),"feedback":g.feedback} for g,a in grades],
        "submissions":[{**submission_json(s),"assignment_title":a.title} for s,a in submissions]}
