import unittest
from uuid import uuid4
from decimal import Decimal
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models import User,Classroom,Enrollment,Assignment,StudentWallet,LedgerEntry
from app.routes.wallets import student_transaction,StudentTransaction,wallet_assignments,account_overview

class StudentBankingTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite:///:memory:');Base.metadata.create_all(self.engine);self.db=sessionmaker(bind=self.engine)()
        self.student=User(id=1,name='Student',email='s@test.edu',password_hash='x',role='student',is_active=True)
        self.teacher=User(id=2,name='Teacher',email='t@test.edu',password_hash='x',role='teacher',is_active=True)
        self.peer=User(id=3,name='Peer',email='s2@test.edu',password_hash='x',role='student',is_active=True)
        self.db.add_all([self.student,self.teacher,self.peer,Classroom(id=1,name='Budgeting',teacher_id=2),Classroom(id=2,name='Savings',teacher_id=2),Enrollment(classroom_id=1,student_id=1,status='active'),Assignment(id=1,classroom_id=1,created_by=2,title='Class event',status='active'),Assignment(id=2,classroom_id=2,created_by=2,title='Savings goal',status='active'),Assignment(id=3,classroom_id=1,created_by=2,title='Closed',status='closed'),Assignment(id=4,classroom_id=1,created_by=2,title='Draft',status='draft'),StudentWallet(id=1,classroom_id=1,student_id=1),StudentWallet(id=2,classroom_id=1,student_id=3),LedgerEntry(wallet_id=1,amount=Decimal('50'),entry_type='deposit',source='teacher_grant')]);self.db.commit()
    def tearDown(self):self.db.close();self.engine.dispose()
    def payload(self,**updates):return StudentTransaction(**({'assignment_id':1,'amount':'12.25','entry_type':'withdrawal','memo':'Event supplies','request_id':str(uuid4())}|updates))
    def balance(self):return self.db.get(StudentWallet,1,populate_existing=True).balance
    def test_expense_and_deposit_reflect_assignment_and_balance(self):
        expense=student_transaction(1,self.payload(),self.db,self.student)
        self.assertEqual(expense.assignment_title,'Class event');self.assertEqual(expense.source,'student_action')
        self.assertEqual(self.balance(),Decimal('37.75'))
        student_transaction(1,self.payload(amount='20.10',entry_type='deposit',memo='Ticket sales'),self.db,self.student)
        self.assertEqual(self.balance(),Decimal('57.85'))
        snapshot=account_overview(self.db,self.student)[0]
        self.assertEqual(snapshot['classroom_name'],'Budgeting');self.assertEqual(snapshot['activity'][0]['assignment_title'],'Class event')
    def test_retries_do_not_duplicate_money(self):
        payload=self.payload();first=student_transaction(1,payload,self.db,self.student);second=student_transaction(1,payload,self.db,self.student)
        self.assertEqual(first.id,second.id);self.assertEqual(self.db.query(LedgerEntry).count(),2);self.assertEqual(self.balance(),Decimal('37.75'))
    def test_reused_request_with_different_amount_rejected(self):
        payload=self.payload();student_transaction(1,payload,self.db,self.student)
        with self.assertRaises(HTTPException):student_transaction(1,self.payload(request_id=payload.request_id,amount='1'),self.db,self.student)
        self.db.rollback();self.assertEqual(self.balance(),Decimal('37.75'))
    def test_other_students_account_is_blocked(self):
        with self.assertRaises(HTTPException) as result:student_transaction(2,self.payload(),self.db,self.student)
        self.assertEqual(result.exception.status_code,403)
        with self.assertRaises(HTTPException):wallet_assignments(2,self.db,self.student)
    def test_assignment_must_match_classroom(self):
        with self.assertRaises(HTTPException):student_transaction(1,self.payload(assignment_id=2),self.db,self.student)
        self.db.rollback();self.assertEqual(self.balance(),Decimal('50'))
    def test_closed_and_draft_assignment_blocked(self):
        for assignment in [3,4]:
            with self.assertRaises(HTTPException):student_transaction(1,self.payload(assignment_id=assignment),self.db,self.student)
            self.db.rollback()
    def test_insufficient_funds_not_recorded(self):
        with self.assertRaises(HTTPException):student_transaction(1,self.payload(amount='50.01'),self.db,self.student)
        self.db.rollback();self.assertEqual(self.balance(),Decimal('50'));self.assertEqual(self.db.query(LedgerEntry).count(),1)
    def test_archived_enrollment_cannot_post(self):
        self.db.query(Enrollment).one().status='archived';self.db.commit()
        with self.assertRaises(HTTPException):student_transaction(1,self.payload(),self.db,self.student)
    def test_assignment_required_and_amount_validated(self):
        for updates in [{'assignment_id':None},{'amount':'0'},{'amount':'-1'},{'amount':'0.001'},{'amount':'NaN'}]:
            with self.assertRaises(ValidationError):self.payload(**updates)
        with self.assertRaises(HTTPException):student_transaction(1,self.payload(memo='   '),self.db,self.student)
    def test_assignment_picker_hides_drafts(self):
        self.assertEqual([a['id'] for a in wallet_assignments(1,self.db,self.student)],[1,3])

if __name__=='__main__':unittest.main()
