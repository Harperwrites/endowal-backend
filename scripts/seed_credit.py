"""Add fictional credit snapshots for existing demo users without resetting data."""
from datetime import date,timedelta
from decimal import Decimal
from app.db.session import SessionLocal
from app.models import User
from app.models.credit import CreditProfile,CreditAccount
from scripts.seed_demo import get_or_create

def seed_credit():
    emails=[f"student{i}@endowal.app" for i in range(1,9)]+["teacher@endowal.app","teacher2@endowal.app","admin@endowal.app"]
    scores=[720,685,760,640,705,790,665,735,780,750,770]
    as_of=date(2026,10,21)
    with SessionLocal() as db:
        count=0
        for i,email in enumerate(emails):
            user=db.query(User).filter_by(email=email).first()
            if not user:continue
            get_or_create(db,CreditProfile,user_id=user.id,defaults={"score":scores[i],"as_of":as_of,"inquiries":i%3})
            for j,name in enumerate(["Endowal Practice Card","Learning Credit Line"]):
                limit=Decimal(500+500*j+100*i)
                ratio=[Decimal('0.20'),Decimal('0.45'),Decimal('0.12'),Decimal('0.60')][(i+j)%4]
                total=12+6*j;late=1 if i in [1,3,6] and j==0 else 0
                get_or_create(db,CreditAccount,user_id=user.id,name=name,defaults={"credit_limit":limit,"balance":(limit*ratio).quantize(Decimal('.01')),"payments_total":total,"payments_on_time":total-late,"opened_on":as_of-timedelta(days=390+180*j+i*10)})
            count+=1
        db.commit();print(f"Fictional credit data ready for {count} demo users. Existing profiles preserved.")

if __name__=="__main__":seed_credit()
