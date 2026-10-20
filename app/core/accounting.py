"""All balance changes are ledger entries; serialize writers per wallet."""
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session
from app.models import StudentWallet

def lock_wallet(db: Session, wallet_id: int) -> StudentWallet:
    # An UPDATE locks the row on Postgres and acquires SQLite's write lock.
    # No read/modify/write of a cached financial total is involved.
    db.execute(update(StudentWallet).where(StudentWallet.id == wallet_id).values(
        legacy_balance=StudentWallet.legacy_balance
    ).execution_options(synchronize_session=False))
    wallet = db.get(StudentWallet, wallet_id, populate_existing=True)
    if wallet is None:
        raise HTTPException(404, "Wallet not found")
    return wallet

def signed(amount, entry_type):
    amount = Decimal(str(amount))
    return amount if entry_type == "deposit" else -amount

def check_balance(wallet, delta):
    result = Decimal(str(wallet.balance)) + delta
    if result < 0:
        raise HTTPException(400, "Insufficient funds for this change")
    if result > Decimal("9999999999.99"):
        raise HTTPException(400, "Account balance exceeds the supported limit")
