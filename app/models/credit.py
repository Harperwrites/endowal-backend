from datetime import date
from decimal import Decimal
from sqlalchemy import Integer, String, Numeric, Date, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class CreditProfile(Base):
    __tablename__="credit_profiles"
    __table_args__=(CheckConstraint("score >= 300 AND score <= 850",name="ck_demo_credit_score"),CheckConstraint("inquiries >= 0",name="ck_credit_inquiries"))
    user_id:Mapped[int]=mapped_column(Integer,primary_key=True)
    score:Mapped[int]=mapped_column(Integer,nullable=False)
    as_of:Mapped[date]=mapped_column(Date,nullable=False)
    inquiries:Mapped[int]=mapped_column(Integer,nullable=False,default=0)

class CreditAccount(Base):
    __tablename__="credit_accounts"
    __table_args__=(CheckConstraint("balance >= 0 AND credit_limit > 0 AND balance <= credit_limit",name="ck_credit_account_amounts"),CheckConstraint("payments_total >= 0 AND payments_on_time >= 0 AND payments_on_time <= payments_total",name="ck_credit_payment_counts"))
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    user_id:Mapped[int]=mapped_column(Integer,nullable=False,index=True)
    name:Mapped[str]=mapped_column(String(120),nullable=False)
    credit_limit:Mapped[Decimal]=mapped_column(Numeric(12,2),nullable=False)
    balance:Mapped[Decimal]=mapped_column(Numeric(12,2),nullable=False)
    payments_total:Mapped[int]=mapped_column(Integer,nullable=False,default=0)
    payments_on_time:Mapped[int]=mapped_column(Integer,nullable=False,default=0)
    opened_on:Mapped[date]=mapped_column(Date,nullable=False)
