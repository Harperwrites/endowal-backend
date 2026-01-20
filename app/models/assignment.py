from sqlalchemy import Date, Enum, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    classroom_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_by: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(80))
    target_amount: Mapped[float | None] = mapped_column(Numeric(12, 2))
    due_date: Mapped[str | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(
        Enum("draft", "active", "closed", name="assignment_status"),
        nullable=False,
        default="draft",
    )
