from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Integer, Numeric, Text, DateTime, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Grade(Base):
    __tablename__ = "grades"
    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", name="uq_grade_assignment_student"),
        CheckConstraint("points_possible > 0 AND points_earned >= 0 AND points_earned <= points_possible", name="ck_grade_points"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assignment_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    graded_by: Mapped[int] = mapped_column(Integer, nullable=False)
    points_earned: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    points_possible: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
