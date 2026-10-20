from sqlalchemy import Integer, Numeric, String, UniqueConstraint, select, func, case
from sqlalchemy.orm import Mapped, mapped_column, column_property
from app.models.ledger import LedgerEntry

from app.db.base import Base


class StudentWallet(Base):
    __tablename__ = "student_wallets"
    __table_args__ = (
        UniqueConstraint("classroom_id", "student_id", name="uq_wallet_class_student"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    classroom_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # Keep the legacy column for schema compatibility; the ledger is authoritative.
    legacy_balance: Mapped[float] = mapped_column("balance", Numeric(12, 2), nullable=False, default=0)
    balance = column_property(
        select(func.coalesce(func.sum(case(
            (LedgerEntry.entry_type == "deposit", LedgerEntry.amount),
            else_=-LedgerEntry.amount,
        )), 0)).where(LedgerEntry.wallet_id == id).correlate_except(LedgerEntry).scalar_subquery()
    )


class WalletBucket(Base):
    __tablename__ = "wallet_buckets"
    __table_args__ = (
        UniqueConstraint("wallet_id", "name", name="uq_bucket_wallet_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wallet_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    percent_target: Mapped[float | None] = mapped_column(Numeric(5, 2))
