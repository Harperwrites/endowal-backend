import unittest
from datetime import date
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.db.base import Base
from app.models import User
from app.models.credit import CreditProfile,CreditAccount
from app.routes.credit import profile,credit_snapshot

class CreditTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite:///:memory:');Base.metadata.create_all(self.engine);self.db=sessionmaker(bind=self.engine)()
        self.user=User(id=1,email='one@test.edu',name='One',password_hash='x',role='student',is_active=True)
        self.other=User(id=2,email='two@test.edu',name='Two',password_hash='x',role='student',is_active=True)
        self.db.add_all([self.user,self.other,CreditProfile(user_id=1,score=720,as_of=date(2026,10,21),inquiries=1),CreditAccount(user_id=1,name='One',credit_limit=Decimal('200'),balance=Decimal('40'),payments_total=12,payments_on_time=11,opened_on=date(2025,10,1)),CreditAccount(user_id=1,name='Two',credit_limit=Decimal('1000'),balance=Decimal('600'),payments_total=18,payments_on_time=18,opened_on=date(2025,1,1))]);self.db.commit()
    def tearDown(self):self.db.close();self.engine.dispose()
    def test_weighted_utilization_and_credit_totals(self):
        data=profile(self.db,self.user)
        self.assertEqual(Decimal(data['balance']),Decimal('640'))
        self.assertEqual(Decimal(data['credit_limit']),Decimal('1200'))
        self.assertEqual(Decimal(data['available_credit']),Decimal('560'))
        self.assertEqual(data['utilization'],53.3)
        self.assertEqual(data['accounts'][0]['utilization'],20.0)
    def test_payment_counts_reconcile(self):
        data=credit_snapshot(self.db,1)
        self.assertEqual(data['payments_total'],30);self.assertEqual(data['payments_on_time'],29)
        self.assertEqual(data['late_payments'],1);self.assertEqual(data['on_time_percentage'],96.7)
    def test_other_user_does_not_receive_profile(self):self.assertIsNone(profile(self.db,self.other))
    def test_simulated_data_clearly_labeled(self):
        self.assertTrue(profile(self.db,self.user)['simulation']);self.assertEqual(profile(self.db,self.user)['score'],720)
    def test_empty_history_has_no_division_by_zero(self):
        self.db.query(CreditAccount).delete();self.db.commit()
        data=profile(self.db,self.user);self.assertIsNone(data['utilization']);self.assertIsNone(data['on_time_percentage'])
    def test_invalid_scores_rejected(self):
        self.db.get(CreditProfile,1).score=900
        with self.assertRaises(IntegrityError):self.db.commit()
        self.db.rollback()
    def test_invalid_account_amounts_rejected(self):
        self.db.query(CreditAccount).first().balance=Decimal('201')
        with self.assertRaises(IntegrityError):self.db.commit()
        self.db.rollback()

if __name__=='__main__':unittest.main()
