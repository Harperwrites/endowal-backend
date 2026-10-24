from typing import Literal
from fastapi import APIRouter,Depends
from pydantic import BaseModel,EmailStr,Field,field_validator
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.deps import require_roles
from app.models import User
from app.models.interest import InterestRequest
router=APIRouter(prefix="/interest",tags=["interest"])
class InterestInput(BaseModel):
    name:str=Field(min_length=1,max_length=120)
    email:EmailStr=Field(max_length=255)
    audience:Literal['investor','donor','school']
    organization:str|None=Field(default=None,max_length=180)
    note:str|None=Field(default=None,max_length=3000)
    @field_validator('name')
    @classmethod
    def name_required(cls,value):
        if not value.strip():raise ValueError('Please enter your name')
        return value.strip()
@router.post('',status_code=201)
def save_interest(payload:InterestInput,db:Session=Depends(get_db)):
    db.add(InterestRequest(**payload.model_dump()));db.commit()
    return {'status':'saved'}
@router.get('')
def list_interest(db:Session=Depends(get_db),user:User=Depends(require_roles('admin'))):
    records=db.query(InterestRequest).order_by(InterestRequest.id.desc()).limit(200).all()
    return [{'id':r.id,'name':r.name,'email':r.email,'audience':r.audience,'organization':r.organization,'note':r.note,'created_at':r.created_at.isoformat()} for r in records]
