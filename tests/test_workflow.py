import unittest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models import User,Classroom,Enrollment,Assignment
from app.models.workflow import AssignmentSubmission
from app.routes.learning import classrooms,classroom_detail,turn_in,TurnIn,student_dashboard
from app.routes.messages import contacts,send,SendMessage,conversation,mark_read

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite:///:memory:');Base.metadata.create_all(self.engine)
        self.db=sessionmaker(bind=self.engine)()
        self.teacher=User(id=1,name='Teacher',email='t@test.edu',password_hash='x',role='teacher',is_active=True)
        self.other_teacher=User(id=2,name='Other Teacher',email='t2@test.edu',password_hash='x',role='teacher',is_active=True)
        self.student=User(id=3,name='Student',email='s@test.edu',password_hash='x',role='student',is_active=True)
        self.peer=User(id=4,name='Peer',email='s2@test.edu',password_hash='x',role='student',is_active=True)
        self.db.add_all([self.teacher,self.other_teacher,self.student,self.peer,
            Classroom(id=1,name='Budgeting',teacher_id=1),Classroom(id=2,name='Other',teacher_id=2),
            Enrollment(classroom_id=1,student_id=3,status='active'),Enrollment(classroom_id=1,student_id=4,status='active'),
            Assignment(id=1,classroom_id=1,created_by=1,title='Budget',status='active'),
            Assignment(id=2,classroom_id=1,created_by=1,title='Draft',status='draft'),
            Assignment(id=3,classroom_id=2,created_by=2,title='Other',status='active')]);self.db.commit()
    def tearDown(self):self.db.close();self.engine.dispose()
    def test_scoped_classrooms(self):
        self.assertEqual([c['id'] for c in classrooms(self.db,self.student)],[1])
        self.assertEqual([c['id'] for c in classrooms(self.db,self.other_teacher)],[2])
    def test_turn_in_and_resubmit(self):
        turn_in(1,TurnIn(content='My budget totals $100.'),self.db,self.student)
        result=turn_in(1,TurnIn(content='Revised budget totals $100.'),self.db,self.student)
        self.assertEqual(self.db.query(AssignmentSubmission).count(),1)
        self.assertEqual(result['content'],'Revised budget totals $100.')
        self.assertEqual(result['student_id'],3)
    def test_classroom_detail_hides_peer_work_and_drafts(self):
        turn_in(1,TurnIn(content='Private peer work'),self.db,self.peer)
        detail=classroom_detail(1,self.db,self.student)
        self.assertEqual(detail['students'],[])
        self.assertEqual([a['id'] for a in detail['assignments']],[1])
        self.assertEqual(detail['assignments'][0]['submissions'],[])
        teacher=classroom_detail(1,self.db,self.teacher)
        self.assertEqual(len(teacher['students']),2)
        self.assertEqual(teacher['assignments'][0]['submissions'][0]['content'],'Private peer work')
    def test_non_enrolled_and_closed_submission_rejected(self):
        with self.assertRaises(HTTPException):turn_in(3,TurnIn(content='No access'),self.db,self.student)
        with self.assertRaises(HTTPException):turn_in(2,TurnIn(content='Draft'),self.db,self.student)
        self.db.get(Assignment,1).status='closed';self.db.commit()
        with self.assertRaises(HTTPException):turn_in(1,TurnIn(content='Closed'),self.db,self.student)
    def test_empty_submission_rejected(self):
        with self.assertRaises(ValidationError):TurnIn(content='  ')
    def test_teacher_student_dashboard_and_other_teacher_denied(self):
        turn_in(1,TurnIn(content='Student work'),self.db,self.student)
        data=student_dashboard(1,3,self.db,self.teacher)
        self.assertEqual(data['submissions'][0]['content'],'Student work')
        with self.assertRaises(HTTPException):student_dashboard(1,3,self.db,self.other_teacher)
        with self.assertRaises(HTTPException):classroom_detail(1,self.db,self.other_teacher)
    def test_chat_roundtrip_and_unread(self):
        send(SendMessage(classroom_id=1,partner_id=1,body='Hello teacher'),self.db,self.student)
        incoming=contacts(self.db,self.teacher)
        self.assertEqual(next(c for c in incoming if c['user_id']==3)['unread'],1)
        thread=conversation(1,3,self.db,self.teacher)
        self.assertEqual(thread[0]['body'],'Hello teacher')
        mark_read(1,3,self.db,self.teacher)
        self.assertEqual(next(c for c in contacts(self.db,self.teacher) if c['user_id']==3)['unread'],0)
        send(SendMessage(classroom_id=1,partner_id=3,body='Hi student'),self.db,self.teacher)
        self.assertEqual(len(conversation(1,1,self.db,self.student)),2)
    def test_chat_not_accessible_to_peer_or_other_teacher(self):
        send(SendMessage(classroom_id=1,partner_id=1,body='Private'),self.db,self.student)
        with self.assertRaises(HTTPException):conversation(1,3,self.db,self.peer)
        with self.assertRaises(HTTPException):conversation(1,3,self.db,self.other_teacher)
        with self.assertRaises(HTTPException):send(SendMessage(classroom_id=1,partner_id=4,body='Peer message'),self.db,self.student)
    def test_empty_message_rejected(self):
        with self.assertRaises(ValidationError):SendMessage(classroom_id=1,partner_id=1,body='  ')
    def test_archive_blocks_classroom_and_chat(self):
        enrollment=self.db.query(Enrollment).filter_by(student_id=3).one();enrollment.status='archived';self.db.commit()
        with self.assertRaises(HTTPException):classroom_detail(1,self.db,self.student)
        with self.assertRaises(HTTPException):send(SendMessage(classroom_id=1,partner_id=1,body='Hello'),self.db,self.student)

if __name__=='__main__':unittest.main()
