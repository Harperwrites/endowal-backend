from datetime import timezone
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.deps import get_current_user
from app.models import User, Classroom, Enrollment, Assignment, Grade, StudentWallet, LedgerEntry
from app.models.workflow import AssignmentSubmission
from app.routes.learning import classrooms
router=APIRouter(prefix="/dashboard",tags=["dashboard"])

def utc(value): return value.replace(tzinfo=timezone.utc)

@router.get("/summary")
def summary(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    rooms=classrooms(db,user); ids=[r['id'] for r in rooms]; student=user.role=="student"
    assignments=db.query(Assignment).filter(Assignment.classroom_id.in_(ids),Assignment.status!="draft").order_by(Assignment.due_date,Assignment.id).all()
    task_ids=[a.id for a in assignments]
    submissions=db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id.in_(task_ids))
    grades=db.query(Grade).filter(Grade.assignment_id.in_(task_ids))
    wallets=db.query(StudentWallet)
    if student:
        submissions=submissions.filter(AssignmentSubmission.student_id==user.id)
        grades=grades.filter(Grade.student_id==user.id)
        wallets=wallets.filter(StudentWallet.student_id==user.id)
    else: wallets=wallets.filter(StudentWallet.classroom_id.in_(ids))
    submitted=submissions.all(); graded=grades.all(); wallet_rows=wallets.all()
    grade_map={(g.assignment_id,g.student_id):g for g in graded}
    submitted_ids={s.assignment_id for s in submitted}
    pending_reviews=sum(1 for s in submitted if (s.assignment_id,s.student_id) not in grade_map or utc(grade_map[(s.assignment_id,s.student_id)].updated_at)<utc(s.submitted_at))
    task_rows=[]
    for a in assignments:
        mine=[s for s in submitted if s.assignment_id==a.id]
        task_rows.append({"id":a.id,"classroom_id":a.classroom_id,"classroom_name":next(r['name'] for r in rooms if r['id']==a.classroom_id),"title":a.title,"due_date":str(a.due_date) if a.due_date else None,"open":a.status in ("active","published"),"submitted":bool(mine),"submission_count":len(mine)})
    activity=db.query(LedgerEntry).filter(LedgerEntry.wallet_id.in_([w.id for w in wallet_rows])).order_by(LedgerEntry.id.desc()).limit(3).all()
    earned=sum((g.points_earned for g in graded),Decimal(0));possible=sum((g.points_possible for g in graded),Decimal(0))
    active_students=db.query(Enrollment.student_id).filter(Enrollment.classroom_id.in_(ids),Enrollment.status=="active").distinct().count()
    return {"balance":str(sum((w.balance for w in wallet_rows),Decimal(0))),"account_count":len(wallet_rows),"classrooms":rooms,"student_count":active_students,
            "assignment_count":len(assignments),"todo_count":sum(1 for a in assignments if a.status in ("active","published") and a.id not in submitted_ids) if student else 0,
            "turned_in_count":len(submitted),"review_count":pending_reviews,"grade_count":len(graded),"earned":str(earned),"possible":str(possible),
            "assignments":task_rows,"activity":[{"id":e.id,"memo":e.memo or e.entry_type,"assignment_title":e.assignment_title,"type":e.entry_type,"amount":str(e.amount)} for e in activity]}
