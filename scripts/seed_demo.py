import argparse
import os
from datetime import date
from decimal import Decimal

from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import (
    Assignment,
    BudgetLineItem,
    BudgetSubmission,
    Classroom,
    Enrollment,
    LedgerEntry,
    StudentWallet,
    User,
    WalletBucket,
)


def get_or_create(db, model, defaults=None, **filters):
    instance = db.query(model).filter_by(**filters).first()
    if instance:
        return instance, False
    payload = {**filters, **(defaults or {})}
    instance = model(**payload)
    db.add(instance)
    db.flush()
    return instance, True


def seed(reset: bool = False) -> None:
    admin_email = os.getenv("ENDOWAL_ADMIN_EMAIL", "admin@endowal.app")
    admin_password = os.getenv("ENDOWAL_ADMIN_PASSWORD", "Admin123!")
    teacher_email = os.getenv("ENDOWAL_TEACHER_EMAIL", "teacher@endowal.app")
    teacher_password = os.getenv("ENDOWAL_TEACHER_PASSWORD", "Teacher123!")
    student_password = os.getenv("ENDOWAL_STUDENT_PASSWORD", "Student123!")
    student_emails = os.getenv(
        "ENDOWAL_STUDENT_EMAILS",
        "student1@endowal.app,student2@endowal.app,student3@endowal.app",
    )
    student_names = os.getenv(
        "ENDOWAL_STUDENT_NAMES",
        "Jordan Lee,Avery Patel,Kai Brooks",
    )
    student_email_list = [email.strip() for email in student_emails.split(",") if email.strip()]
    student_name_list = [name.strip() for name in student_names.split(",") if name.strip()]
    if len(student_name_list) < len(student_email_list):
        student_name_list.extend(
            [f"Student {idx}" for idx in range(len(student_name_list) + 1, len(student_email_list) + 1)]
        )

    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin, _ = get_or_create(
            db,
            User,
            email=admin_email,
            defaults={
                "name": "Admin User",
                "role": "admin",
                "is_active": True,
                "password_hash": get_password_hash(admin_password),
            },
        )
        teacher, _ = get_or_create(
            db,
            User,
            email=teacher_email,
            defaults={
                "name": "Ms. Rivera",
                "role": "teacher",
                "is_active": True,
                "password_hash": get_password_hash(teacher_password),
            },
        )
        students = []
        for idx, (email, name) in enumerate(zip(student_email_list, student_name_list), start=1):
            student, _ = get_or_create(
                db,
                User,
                email=email,
                defaults={
                    "name": name,
                    "role": "student",
                    "is_active": True,
                    "password_hash": get_password_hash(student_password),
                },
            )
            students.append(student)

        classroom, _ = get_or_create(
            db,
            Classroom,
            teacher_id=teacher.id,
            name="Budgeting Basics",
            defaults={"school_name": "Endowal Academy", "grade_level": "6"},
        )

        for student in students:
            get_or_create(
                db,
                Enrollment,
                classroom_id=classroom.id,
                student_id=student.id,
            )

        assignments = []
        for title, category, amount in [
            ("Weekly Budget Challenge", "Budgeting", Decimal("100.00")),
            ("Savings Goal Sprint", "Savings", Decimal("250.00")),
        ]:
            assignment, _ = get_or_create(
                db,
                Assignment,
                classroom_id=classroom.id,
                created_by=teacher.id,
                title=title,
                defaults={
                    "description": "Plan your spending and savings using the Endowal wallet.",
                    "category": category,
                    "target_amount": amount,
                    "due_date": date.today(),
                    "status": "active",
                },
            )
            assignments.append(assignment)

        for student in students:
            wallet, _ = get_or_create(
                db,
                StudentWallet,
                classroom_id=classroom.id,
                student_id=student.id,
                defaults={"balance": Decimal("0.00")},
            )
            for name, percent in [("Needs", Decimal("50.00")), ("Wants", Decimal("30.00")), ("Goals", Decimal("20.00"))]:
                get_or_create(
                    db,
                    WalletBucket,
                    wallet_id=wallet.id,
                    name=name,
                    defaults={"percent_target": percent},
                )

            get_or_create(
                db,
                LedgerEntry,
                wallet_id=wallet.id,
                assignment_id=assignments[0].id,
                amount=Decimal("50.00"),
                entry_type="deposit",
                source="teacher_grant",
                defaults={"memo": "Classroom grant"},
            )
            get_or_create(
                db,
                LedgerEntry,
                wallet_id=wallet.id,
                assignment_id=assignments[0].id,
                amount=Decimal("12.00"),
                entry_type="withdrawal",
                source="student_action",
                defaults={"memo": "Snack purchase"},
            )

            submission, _ = get_or_create(
                db,
                BudgetSubmission,
                assignment_id=assignments[0].id,
                student_id=student.id,
                defaults={
                    "total_planned": Decimal("100.00"),
                    "notes": "Split into needs/wants/goals.",
                    "status": "submitted",
                },
            )
            get_or_create(
                db,
                BudgetLineItem,
                submission_id=submission.id,
                category="Supplies",
                defaults={"amount": Decimal("40.00")},
            )
            get_or_create(
                db,
                BudgetLineItem,
                submission_id=submission.id,
                category="Snacks",
                defaults={"amount": Decimal("30.00")},
            )
            get_or_create(
                db,
                BudgetLineItem,
                submission_id=submission.id,
                category="Savings",
                defaults={"amount": Decimal("30.00")},
            )

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Endowal demo data.")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate tables before seeding.")
    args = parser.parse_args()
    seed(reset=args.reset)
