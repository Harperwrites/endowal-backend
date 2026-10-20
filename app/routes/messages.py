from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.deps import get_current_user
from app.models import Classroom, Enrollment, User
from app.models.workflow import Message, now
from app.routes.learning import access, timestamp
router=APIRouter(prefix="/messages",tags=["messages"])

def partner_access(db, classroom_id, partner_id, user):
    room=access(db,classroom_id,user)
    partner=db.get(User,partner_id)
    if not partner or not partner.is_active or partner.id==user.id: raise HTTPException(403,"Invalid conversation recipient")
    if user.role=="student" and partner.id==room.teacher_id: return
    if user.role in ("teacher","admin") and partner.role=="student" and db.query(Enrollment).filter_by(classroom_id=room.id,student_id=partner.id,status="active").first(): return
    raise HTTPException(403,"Messages must be between a classroom teacher and an enrolled student")

@router.get("/contacts")
def contacts(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    rooms=db.query(Classroom)
    if user.role=="teacher": rooms=rooms.filter(Classroom.teacher_id==user.id)
    elif user.role=="student": rooms=rooms.join(Enrollment,Enrollment.classroom_id==Classroom.id).filter(Enrollment.student_id==user.id,Enrollment.status=="active")
    elif user.role!="admin": raise HTTPException(403,"Not authorized")
    result=[]
    for room in rooms.order_by(Classroom.id).all():
        partners=[db.get(User,room.teacher_id)] if user.role=="student" else db.query(User).join(Enrollment,Enrollment.student_id==User.id).filter(Enrollment.classroom_id==room.id,Enrollment.status=="active",User.role=="student").order_by(User.name).all()
        for p in partners:
            if not p or not p.is_active: continue
            unread=db.query(Message).filter_by(classroom_id=room.id,sender_id=p.id,recipient_id=user.id,read_at=None).count()
            result.append({"classroom_id":room.id,"classroom_name":room.name,"user_id":p.id,"name":p.name,"role":p.role,"unread":unread})
    return result

@router.get("")
def conversation(classroom_id:int, partner_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    partner_access(db,classroom_id,partner_id,user)
    query=db.query(Message).filter(Message.classroom_id==classroom_id,or_(and_(Message.sender_id==user.id,Message.recipient_id==partner_id),and_(Message.sender_id==partner_id,Message.recipient_id==user.id)))
    rows=query.order_by(Message.id.desc()).limit(200).all()
    return [{"id":m.id,"sender_id":m.sender_id,"body":m.body,"sent_at":timestamp(m.sent_at)} for m in reversed(rows)]

class SendMessage(BaseModel):
    classroom_id:int
    partner_id:int
    body:str=Field(min_length=1,max_length=5000)
    @field_validator("body")
    @classmethod
    def nonempty(cls,value):
        if not value.strip(): raise ValueError("Write a message")
        return value.strip()

@router.post("")
def send(payload:SendMessage,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    partner_access(db,payload.classroom_id,payload.partner_id,user)
    m=Message(classroom_id=payload.classroom_id,sender_id=user.id,recipient_id=payload.partner_id,body=payload.body)
    db.add(m);db.commit();db.refresh(m)
    return {"id":m.id}

@router.post("/read")
def mark_read(classroom_id:int,partner_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    partner_access(db,classroom_id,partner_id,user)
    db.query(Message).filter_by(classroom_id=classroom_id,sender_id=partner_id,recipient_id=user.id,read_at=None).update({"read_at":now()})
    db.commit()
    return {"status":"read"}
