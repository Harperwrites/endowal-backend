from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.deps import get_current_user
from app.models import User
from app.models.credit import CreditProfile,CreditAccount
router=APIRouter(prefix="/credit",tags=["credit"])

def percentage(numerator,denominator):
    return float((Decimal(numerator)/Decimal(denominator)*100).quantize(Decimal('0.1'),rounding=ROUND_HALF_UP)) if denominator else None

def credit_snapshot(db,user_id):
    profile=db.get(CreditProfile,user_id)
    if not profile:return None
    accounts=db.query(CreditAccount).filter_by(user_id=user_id).order_by(CreditAccount.id).all()
    balance=sum((a.balance for a in accounts),Decimal(0));limit=sum((a.credit_limit for a in accounts),Decimal(0))
    payments=sum(a.payments_total for a in accounts);on_time=sum(a.payments_on_time for a in accounts)
    return {"simulation":True,"score":profile.score,"as_of":str(profile.as_of),"inquiries":profile.inquiries,
            "balance":str(balance),"credit_limit":str(limit),"available_credit":str(limit-balance),"utilization":percentage(balance,limit),
            "payments_total":payments,"payments_on_time":on_time,"late_payments":payments-on_time,"on_time_percentage":percentage(on_time,payments),
            "accounts":[{"id":a.id,"name":a.name,"balance":str(a.balance),"credit_limit":str(a.credit_limit),"available_credit":str(a.credit_limit-a.balance),"utilization":percentage(a.balance,a.credit_limit),"payments_total":a.payments_total,"payments_on_time":a.payments_on_time,"late_payments":a.payments_total-a.payments_on_time,"opened_on":str(a.opened_on)} for a in accounts]}

@router.get("/profile")
def profile(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    # No client-supplied user ID: every signed-in user sees only their own profile.
    return credit_snapshot(db,user.id)
