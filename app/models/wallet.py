from sqlalchemy import Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StudentWallet(Base):
    __tablename__ = "student_wallets"
    __table_args__ = (
        UniqueConstraint("classroom_id", "student_id", name="uq_wallet_class_student"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    classroom_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)


class WalletBucket(Base):
    __tablename__ = "wallet_buckets"
    __table_args__ = (
        UniqueConstraint("wallet_id", "name", name="uq_bucket_wallet_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wallet_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    percent_target: Mapped[float | None] = mapped_column(Numeric(5, 2))
