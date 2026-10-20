import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models import Classroom, User, StudentWallet, LedgerEntry
from app.routes.wallets import create_wallet, update_wallet, transfer, TransferRequest, account_overview
from app.routes.ledger_entries import create_ledger_entry, update_ledger_entry, delete_ledger_entry
from app.schemas.wallet import StudentWalletCreate, StudentWalletUpdate
from app.schemas.ledger import LedgerEntryCreate, LedgerEntryUpdate

class AccountingTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.engine = create_engine('sqlite:///' + str(Path(self.folder.name) / 'test.db'))
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, autoflush=False)
        self.db = self.sessions()
        self.teacher = User(id=1, email='teacher@test.edu', name='Teacher', password_hash='test', role='teacher', is_active=True)
        self.student = User(id=2, email='student@test.edu', name='Student', password_hash='test', role='student', is_active=True)
        self.db.add_all([self.teacher, self.student, Classroom(id=1,teacher_id=1,name='Test')]); self.db.commit()
        self.wallet = create_wallet(StudentWalletCreate(classroom_id=1,student_id=2,balance='50.00'), self.db, self.teacher)
    def tearDown(self):
        self.db.close(); self.engine.dispose(); self.folder.cleanup()
    def balance(self, wallet=None):
        return self.db.get(StudentWallet, wallet or self.wallet.id, populate_existing=True).balance
    def post(self, amount, kind='deposit'):
        return create_ledger_entry(LedgerEntryCreate(wallet_id=self.wallet.id,amount=amount,entry_type=kind,source='teacher_grant'),self.db,self.teacher)
    def test_opening_balance_is_activity(self):
        self.assertEqual(self.balance(),Decimal('50.00'))
        self.assertEqual(self.db.query(LedgerEntry).count(),1)
    def test_deposit_withdrawal_and_cents(self):
        self.post('12.00','withdrawal'); self.post('0.10'); self.post('0.20')
        self.assertEqual(self.balance(),Decimal('38.30'))
    def test_edit_changes_balance_by_difference(self):
        entry=self.post('12.00','withdrawal')
        update_ledger_entry(entry.id,LedgerEntryUpdate(amount='10.00'),self.db,self.teacher)
        self.assertEqual(self.balance(),Decimal('40.00'))
        update_ledger_entry(entry.id,LedgerEntryUpdate(entry_type='deposit'),self.db,self.teacher)
        self.assertEqual(self.balance(),Decimal('60.00'))
    def test_delete_reverses_effect(self):
        entry=self.post('12.00','withdrawal'); delete_ledger_entry(entry.id,self.db,self.teacher)
        self.assertEqual(self.balance(),Decimal('50.00'))
    def test_overdraft_rolls_back(self):
        with self.assertRaises(HTTPException): self.post('50.01','withdrawal')
        self.db.rollback(); self.assertEqual(self.balance(),Decimal('50.00'))
        self.assertEqual(self.db.query(LedgerEntry).count(),1)
    def test_edit_or_delete_cannot_overdraw(self):
        opening=self.db.query(LedgerEntry).first(); self.post('40.00','withdrawal')
        with self.assertRaises(HTTPException): update_ledger_entry(opening.id,LedgerEntryUpdate(amount='30.00'),self.db,self.teacher)
        self.db.rollback()
        with self.assertRaises(HTTPException): delete_ledger_entry(opening.id,self.db,self.teacher)
        self.db.rollback(); self.assertEqual(self.balance(),Decimal('10.00'))
    def test_invalid_money_and_types(self):
        for amount in ['0','-1','0.001','NaN','Infinity','10000000000']:
            with self.assertRaises(ValidationError): LedgerEntryCreate(wallet_id=1,amount=amount,entry_type='deposit',source='teacher_grant')
        with self.assertRaises(ValidationError): LedgerEntryCreate(wallet_id=1,amount=1,entry_type='oops',source='teacher_grant')
    def test_direct_balance_edit_rejected(self):
        with self.assertRaises(HTTPException): update_wallet(self.wallet.id,StudentWalletUpdate(balance=900),self.db,self.teacher)
        self.db.rollback(); self.assertEqual(self.balance(),Decimal('50.00'))
    def test_transfer_conserves_total(self):
        recipient=create_wallet(StudentWalletCreate(classroom_id=1,student_id=3,balance=0),self.db,self.teacher)
        transfer(TransferRequest(from_wallet_id=self.wallet.id,to_wallet_id=recipient.id,amount='12.34'),self.db,self.teacher)
        self.assertEqual(self.balance(),Decimal('37.66')); self.assertEqual(self.balance(recipient.id),Decimal('12.34'))
    def test_transfer_entries_cannot_be_edited_individually(self):
        recipient=create_wallet(StudentWalletCreate(classroom_id=1,student_id=3,balance=0),self.db,self.teacher)
        transfer(TransferRequest(from_wallet_id=self.wallet.id,to_wallet_id=recipient.id,amount='10'),self.db,self.teacher)
        entry=self.db.query(LedgerEntry).filter(LedgerEntry.transfer_id.is_not(None)).first()
        with self.assertRaises(HTTPException): update_ledger_entry(entry.id,LedgerEntryUpdate(amount='20'),self.db,self.teacher)
        self.db.rollback()
        with self.assertRaises(HTTPException): delete_ledger_entry(entry.id,self.db,self.teacher)
        self.db.rollback(); self.assertEqual(self.balance()+self.balance(recipient.id),Decimal('50'))
    def test_failed_transfer_has_no_partial_entries(self):
        recipient=create_wallet(StudentWalletCreate(classroom_id=1,student_id=3,balance=0),self.db,self.teacher)
        with self.assertRaises(HTTPException): transfer(TransferRequest(from_wallet_id=self.wallet.id,to_wallet_id=recipient.id,amount='51'),self.db,self.teacher)
        self.db.rollback(); self.assertEqual(self.balance(),Decimal('50')); self.assertEqual(self.balance(recipient.id),0)
    def test_snapshot_has_balance_and_signed_activity(self):
        self.post('12','withdrawal')
        accounts=account_overview(self.db,self.student)
        self.assertEqual(len(accounts),1); self.assertEqual(Decimal(accounts[0]['balance']),Decimal('38'))
        entries=accounts[0]['activity']
        self.assertEqual(sum(Decimal(e['amount'])*(1 if e['entry_type']=='deposit' else -1) for e in entries),Decimal('38'))
    def test_latest_activity_is_not_truncated_to_oldest(self):
        for _ in range(12): self.post('1')
        accounts=account_overview(self.db,self.student)
        self.assertEqual(len(accounts[0]['activity']),10)
        self.assertEqual(accounts[0]['activity'][0]['id'],13)
        self.assertEqual(Decimal(accounts[0]['balance']),62)
    def test_concurrent_withdrawals_cannot_overdraw(self):
        wallet_id=self.wallet.id; self.db.rollback()
        def withdraw(_):
            with self.sessions() as db:
                teacher=db.get(User,1)
                try:
                    create_ledger_entry(LedgerEntryCreate(wallet_id=wallet_id,amount='40',entry_type='withdrawal',source='teacher_grant'),db,teacher)
                    return True
                except HTTPException:
                    db.rollback(); return False
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(withdraw,range(2)))
        self.assertEqual(sum(results),1); self.assertEqual(self.balance(),Decimal('10'))

if __name__=='__main__': unittest.main()
