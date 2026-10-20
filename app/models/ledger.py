from sqlalchemy import Enum, Integer, Numeric, String, select
from sqlalchemy.orm import Mapped, mapped_column, column_property
from app.models.assignment import Assignment

from app.db.base import Base


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wallet_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    assignment_id: Mapped[int | None] = mapped_column(Integer, index=True)
    assignment_title = column_property(select(Assignment.title).where(Assignment.id == assignment_id).correlate_except(Assignment).scalar_subquery())
    client_request_id: Mapped[str | None] = mapped_column(String(36), unique=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    entry_type: Mapped[str] = mapped_column(
        Enum("deposit", "withdrawal", name="ledger_entry_type"),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(
        Enum("teacher_grant", "student_action", name="ledger_entry_source"),
        nullable=False,
    )
    transfer_id: Mapped[str | None] = mapped_column(String(36), index=True)
    memo: Mapped[str | None] = mapped_column(String(255))
