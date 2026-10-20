"""Add demo workflow data without clearing existing records. Safe to rerun."""
from datetime import date, timedelta
from decimal import Decimal
import os
from app.db.session import SessionLocal
from app.models import User, Classroom, Enrollment, Assignment, StudentWallet, LedgerEntry, Grade
from app.models.workflow import AssignmentSubmission, Message
from app.core.security import get_password_hash
from scripts.seed_demo import get_or_create, seed

def seed_workflow():
    seed()
    base = date.fromisoformat(os.getenv("ENDOWAL_DEMO_DATE", "2026-10-19"))
    with SessionLocal() as db:
        teachers=[]
        for email,name in [("teacher@endowal.app","Ms. Rivera"),("teacher2@endowal.app","Mr. Chen")]:
            t,_=get_or_create(db,User,email=email,defaults={"name":name,"role":"teacher","is_active":True,"password_hash":get_password_hash("Teacher123!")})
            teachers.append(t)
        students=[]
        for index,name in enumerate(["Jordan Lee","Avery Patel","Kai Brooks","Morgan Davis","Riley Chen","Sam Taylor","Alex Rivera","Casey Nguyen"],1):
            s,_=get_or_create(db,User,email=f"student{index}@endowal.app",defaults={"name":name,"role":"student","is_active":True,"password_hash":get_password_hash("Student123!")})
            students.append(s)
        plans=[(teachers[0],"Budgeting Basics",students[:4],"6"),(teachers[0],"Savings & Goals",students[0:6:2],"7"),(teachers[1],"Money Lab",students[4:],"8"),(teachers[1],"Entrepreneur Studio",students[1::2],"8")]
        topics=[("Needs vs. Wants","Build a $100 weekly budget. List three needs, two wants, and a savings amount. Show that your amounts total $100 and explain one trade-off."),
                ("My Savings Plan","Choose a $120 savings goal. Plan how much to save each week for six weeks. Show your calculations and explain how you will handle an unexpected expense."),
                ("Plan a Class Event","Plan a class event with a $250 budget. Itemize the costs, reserve $25 for surprises, and explain how you kept your total within the budget.")]
        for ci,(teacher,name,roster,grade_level) in enumerate(plans):
            room,_=get_or_create(db,Classroom,teacher_id=teacher.id,name=name,defaults={"school_name":"Endowal Academy","grade_level":grade_level})
            assignments=[]
            for ai,(title,description) in enumerate(topics):
                a,_=get_or_create(db,Assignment,classroom_id=room.id,created_by=teacher.id,title=title,defaults={"description":description,"category":"Financial literacy","target_amount":Decimal([100,120,250][ai]),"due_date":base+timedelta(days=3+ai*4),"status":"active"})
                assignments.append(a)
            for si,student in enumerate(roster):
                get_or_create(db,Enrollment,classroom_id=room.id,student_id=student.id,defaults={"status":"active"})
                wallet,_=get_or_create(db,StudentWallet,classroom_id=room.id,student_id=student.id)
                if not db.query(LedgerEntry).filter_by(wallet_id=wallet.id).first():
                    db.add(LedgerEntry(wallet_id=wallet.id,amount=Decimal(75+si*10),entry_type="deposit",source="teacher_grant",memo="Demo classroom opening grant"))
                    db.add(LedgerEntry(wallet_id=wallet.id,amount=Decimal("8.50"),entry_type="withdrawal",source="student_action",memo="Demo classroom supplies"))
                if si%2==0:
                    work,_=get_or_create(db,AssignmentSubmission,assignment_id=assignments[0].id,student_id=student.id,defaults={"content":"My $100 budget: supplies $25, lunch $20, bus fare $15, entertainment $10, treats $10, and savings $20. Total = $100. I chose to save $20 by limiting entertainment and treats to $20 combined."})
                    get_or_create(db,Grade,assignment_id=assignments[0].id,student_id=student.id,defaults={"graded_by":teacher.id,"points_earned":Decimal(88+si),"points_possible":Decimal(100),"feedback":"Your total is accurate. Add more detail about how you separated needs from wants."})
                elif si%3==0:
                    get_or_create(db,AssignmentSubmission,assignment_id=assignments[1].id,student_id=student.id,defaults={"content":"I want to save $120 for a bike repair. $120 / 6 weeks = $20 per week. I will save a little extra when I can to cover unexpected costs."})
                for sender,recipient,body in [(teacher,student,f"Welcome to {room.name}! Open Assignments to view the missions, and send me a message if you need help."),(student,teacher,"Thanks! I can see the assignments. Could you check my budget explanation when I turn it in?")]:
                    get_or_create(db,Message,classroom_id=room.id,sender_id=sender.id,recipient_id=recipient.id,body=body)
        db.commit()
        print("Workflow demo ready: 2 teachers, 8 students, 4 classrooms plus existing data.")
        print("Teachers: teacher@endowal.app / teacher2@endowal.app — Teacher123!")
        print("Students: student1@endowal.app through student8@endowal.app — Student123!")

if __name__=="__main__": seed_workflow()
