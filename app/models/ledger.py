from sqlalchemy import Enum, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wallet_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    assignment_id: Mapped[int | None] = mapped_column(Integer, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    entry_type: Mapped[str] = mapped_column(
        Enum("deposit", "withdrawal", name="ledger_entry_type"),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(
        Enum("teacher_grant", "student_action", name="ledger_entry_source"),
        nullable=False,
    )
    memo: Mapped[str | None] = mapped_column(String(255))
