"""Opt-in fictional hosted demo. Never resets data or changes existing passwords."""
import os
from datetime import date, timedelta
from decimal import Decimal

from app.core.config import settings
from app.core.deployment import verify_client_database
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models import User, Classroom, Enrollment, Assignment, StudentWallet, LedgerEntry, Grade
from app.models.workflow import AssignmentSubmission
from app.models.credit import CreditProfile, CreditAccount
from scripts.seed_demo import get_or_create


def main():
    if os.getenv("ENDOWAL_SEED_HOSTED_DEMO") != "true":
        print("Hosted demo seeding disabled.")
        return
    if settings.client_id != "endowal" or settings.deployment_environment != "production":
        raise RuntimeError("Hosted demo requires the Endowal production deployment")
    passwords = [os.getenv("ENDOWAL_DEMO_TEACHER_PASSWORD", ""), os.getenv("ENDOWAL_DEMO_STUDENT_PASSWORD", "")]
    if any(len(p) < 16 or len(p.encode()) > 72 for p in passwords) or passwords[0] == passwords[1]:
        raise ValueError("Set distinct demo teacher/student passwords, 16+ characters and at most 72 bytes")
    verify_client_database()
    with SessionLocal() as db:
        def account(email, name, role, password):
            user = db.query(User).filter_by(email=email).first()
            if user:
                if user.role != role or user.name != name:
                    raise ValueError("Demo email conflicts with an existing account; no changes committed")
                return user
            return get_or_create(db, User, email=email, defaults=dict(name=name, role=role, is_active=True, password_hash=get_password_hash(password)))[0]

        teachers = [account(f"demo.teacher{i}@endowal.app", name, "teacher", passwords[0]) for i, name in enumerate(["Demo Ms. Rivera", "Demo Mr. Chen"], 1)]
        students = [account(f"demo.student{i}@endowal.app", f"Demo {name}", "student", passwords[1]) for i, name in enumerate(["Jordan Lee", "Avery Patel", "Kai Brooks", "Morgan Davis", "Riley Chen", "Sam Taylor", "Alex Rivera", "Casey Nguyen"], 1)]
        topics = [("Needs vs. Wants", "Build a $100 budget with needs, wants, and savings. Explain a trade-off.", 100), ("My Savings Plan", "Plan a $120 savings goal over six weeks. Show your calculations.", 120), ("Plan a Class Event", "Plan a $250 event, reserving $25 for surprises.", 250)]
        for index, name in enumerate(["Budgeting Basics", "Savings & Goals", "Money Lab", "Entrepreneur Studio"]):
            teacher = teachers[index // 2]
            room, _ = get_or_create(db, Classroom, teacher_id=teacher.id, name=f"Demo · {name}", defaults=dict(school_name="Fictional Endowal Academy", grade_level="7"))
            tasks = [get_or_create(db, Assignment, classroom_id=room.id, created_by=teacher.id, title=title, defaults=dict(description=description, category="Financial literacy", target_amount=Decimal(amount), due_date=date.today()+timedelta(days=7+4*j), status="active"))[0] for j, (title, description, amount) in enumerate(topics)]
            for offset, student in enumerate(students[index % 2::2]):
                get_or_create(db, Enrollment, classroom_id=room.id, student_id=student.id, defaults=dict(status="active"))
                wallet, _ = get_or_create(db, StudentWallet, classroom_id=room.id, student_id=student.id)
                if not db.query(LedgerEntry).filter_by(wallet_id=wallet.id).first():
                    db.add(LedgerEntry(wallet_id=wallet.id, assignment_id=tasks[0].id, amount=Decimal("100"), entry_type="deposit", source="teacher_grant", memo="Fictional demo opening grant"))
                    db.add(LedgerEntry(wallet_id=wallet.id, assignment_id=tasks[0].id, amount=Decimal("8.50"), entry_type="withdrawal", source="student_action", memo="Fictional demo supplies"))
                if offset % 2 == 0:
                    get_or_create(db, AssignmentSubmission, assignment_id=tasks[0].id, student_id=student.id, defaults=dict(content="Needs $60 + wants $20 + savings $20 = $100. I limited wants to save more."))
                    get_or_create(db, Grade, assignment_id=tasks[0].id, student_id=student.id, defaults=dict(graded_by=teacher.id, points_earned=Decimal("90"), points_possible=Decimal("100"), feedback="Accurate total! Explain each need."))
        for i, student in enumerate(students):
            get_or_create(db, CreditProfile, user_id=student.id, defaults=dict(score=650+i*18, as_of=date.today(), inquiries=i%3))
            get_or_create(db, CreditAccount, user_id=student.id, name="Fictional Practice Card", defaults=dict(credit_limit=Decimal("1000"), balance=Decimal(100+i*30), payments_total=12, payments_on_time=12-i%2, opened_on=date.today()-timedelta(days=400)))
        db.commit()
    print("Hosted fictional demo ready: 2 teachers, 8 students, 4 classrooms. Existing records preserved.")


if __name__ == "__main__":
    main()
