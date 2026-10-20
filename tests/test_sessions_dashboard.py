import unittest
from datetime import datetime,timedelta,timezone
from decimal import Decimal
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models import User,Classroom,Enrollment,Assignment,Grade,StudentWallet,LedgerEntry
from app.models.auth_session import AuthSession
from app.models.workflow import AssignmentSubmission
from app.core.sessions import COOKIE,remember,session_user,digest
from app.routes.auth import refresh,logout,remember_device
from app.routes.dashboard import summary

def request(token=None):
    headers=[] if token is None else [(b'cookie',f'{COOKIE}={token}'.encode())]
    return Request({'type':'http','scheme':'http','server':('127.0.0.1',8000),'path':'/auth','headers':headers})

class SessionDashboardTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite:///:memory:');Base.metadata.create_all(self.engine);self.db=sessionmaker(bind=self.engine)()
        self.user=User(id=1,name='Student',email='s@test.edu',password_hash='x',role='student',is_active=True)
        self.teacher=User(id=2,name='Teacher',email='t@test.edu',password_hash='x',role='teacher',is_active=True)
        self.other=User(id=3,name='Other',email='t2@test.edu',password_hash='x',role='teacher',is_active=True)
        self.db.add_all([self.user,self.teacher,self.other,Classroom(id=1,name='Finance',teacher_id=2),Classroom(id=2,name='Other',teacher_id=3),Enrollment(classroom_id=1,student_id=1,status='active'),Assignment(id=1,classroom_id=1,created_by=2,title='Budget',status='active'),Assignment(id=2,classroom_id=2,created_by=3,title='Other',status='active'),StudentWallet(id=1,classroom_id=1,student_id=1),LedgerEntry(wallet_id=1,amount=Decimal('50'),entry_type='deposit',source='teacher_grant'),LedgerEntry(wallet_id=1,amount=Decimal('12'),entry_type='withdrawal',source='student_action')]);self.db.commit()
    def tearDown(self):self.db.close();self.engine.dispose()
    def remembered(self):
        response=Response();remember(self.db,self.user,request(),response)
        cookie=response.headers['set-cookie'];token=cookie.split(';')[0].split('=',1)[1]
        return token,cookie
    def test_remembered_cookie_is_http_only_and_hashed(self):
        token,cookie=self.remembered()
        self.assertIn('HttpOnly',cookie);self.assertIn('Max-Age=2592000',cookie);self.assertIn('SameSite=lax',cookie)
        self.assertEqual(self.db.query(AuthSession).one().token_hash,digest(token))
        self.assertNotEqual(self.db.query(AuthSession).one().token_hash,token)
        self.assertEqual(session_user(self.db,token).id,1)
    def test_refresh_restores_without_password(self):
        token,_=self.remembered();result=refresh(request(token),self.db)
        self.assertTrue(result.access_token)
    def test_same_browser_session_reused(self):
        token,_=self.remembered();remember(self.db,self.user,request(token),Response())
        self.assertEqual(self.db.query(AuthSession).count(),1)
    def test_logout_revokes_remembered_session(self):
        token,_=self.remembered();response=Response();logout(request(token),response,self.db)
        self.assertIsNone(session_user(self.db,token));self.assertIn('Max-Age=0',response.headers['set-cookie'])
        with self.assertRaises(HTTPException):refresh(request(token),self.db)
    def test_revoked_cookie_cannot_be_recreated_by_pending_remember(self):
        token,_=self.remembered();logout(request(token),Response(),self.db)
        with self.assertRaises(HTTPException):remember_device(request(token),Response(),self.db,self.user)
        self.assertEqual(self.db.query(AuthSession).count(),0)
    def test_expired_session_cannot_refresh(self):
        token,_=self.remembered();self.db.query(AuthSession).one().expires_at=datetime.now(timezone.utc)-timedelta(seconds=1);self.db.commit()
        with self.assertRaises(HTTPException):refresh(request(token),self.db)
    def test_inactive_account_cannot_refresh(self):
        token,_=self.remembered();self.user.is_active=False;self.db.commit()
        self.assertIsNone(session_user(self.db,token))
    def test_missing_and_forged_cookie_rejected(self):
        for token in [None,'made-up']:
            with self.assertRaises(HTTPException):refresh(request(token),self.db)
    def test_student_summary_uses_live_ledger_and_scoped_work(self):
        data=summary(self.db,self.user)
        self.assertEqual(Decimal(data['balance']),Decimal('38'))
        self.assertEqual(data['todo_count'],1);self.assertEqual(data['grade_count'],0)
        self.assertEqual([a['id'] for a in data['assignments']],[1])
    def test_teacher_only_sees_own_classroom_funds(self):
        self.assertEqual(Decimal(summary(self.db,self.teacher)['balance']),Decimal('38'))
        self.assertEqual(Decimal(summary(self.db,self.other)['balance']),0)
    def test_submission_and_grade_update_summary(self):
        self.db.add(AssignmentSubmission(assignment_id=1,student_id=1,content='Work'))
        self.db.commit()
        self.assertEqual(summary(self.db,self.teacher)['review_count'],1)
        self.db.add(Grade(assignment_id=1,student_id=1,graded_by=2,points_earned=Decimal('9'),points_possible=Decimal('10')));self.db.commit()
        data=summary(self.db,self.user)
        self.assertEqual(data['todo_count'],0);self.assertEqual(data['turned_in_count'],1)
        self.assertEqual(Decimal(data['earned']),Decimal('9'));self.assertEqual(Decimal(data['possible']),Decimal('10'))
        self.assertEqual(summary(self.db,self.teacher)['review_count'],0)

if __name__=='__main__':unittest.main()
