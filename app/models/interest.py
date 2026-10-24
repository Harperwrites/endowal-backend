from datetime import datetime,timezone
from sqlalchemy import Integer,String,Text,DateTime
from sqlalchemy.orm import Mapped,mapped_column
from app.db.base import Base
class InterestRequest(Base):
    __tablename__="interest_requests"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    name:Mapped[str]=mapped_column(String(120),nullable=False)
    email:Mapped[str]=mapped_column(String(255),nullable=False)
    audience:Mapped[str]=mapped_column(String(20),nullable=False)
    organization:Mapped[str|None]=mapped_column(String(180))
    note:Mapped[str|None]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,default=lambda:datetime.now(timezone.utc))
