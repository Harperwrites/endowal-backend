from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import StudentWallet
from app.schemas.wallet import (
    StudentWalletCreate,
    StudentWalletOut,
    StudentWalletUpdate,
)

router = APIRouter(prefix="/wallets", tags=["wallets"])


def _get_or_404(db: Session, wallet_id: int) -> StudentWallet:
    wallet = db.get(StudentWallet, wallet_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet


@router.get("", response_model=list[StudentWalletOut])
def list_wallets(
    skip: int = 0,
    limit: int = 100,
    classroom_id: int | None = None,
    student_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(StudentWallet)
    if classroom_id is not None:
        query = query.filter(StudentWallet.classroom_id == classroom_id)
    if student_id is not None:
        query = query.filter(StudentWallet.student_id == student_id)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=StudentWalletOut, status_code=status.HTTP_201_CREATED)
def create_wallet(payload: StudentWalletCreate, db: Session = Depends(get_db)):
    wallet = StudentWallet(**payload.model_dump())
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet


@router.get("/{wallet_id}", response_model=StudentWalletOut)
def get_wallet(wallet_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, wallet_id)


@router.patch("/{wallet_id}", response_model=StudentWalletOut)
def update_wallet(
    wallet_id: int, payload: StudentWalletUpdate, db: Session = Depends(get_db)
):
    wallet = _get_or_404(db, wallet_id)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(wallet, key, value)
    db.commit()
    db.refresh(wallet)
    return wallet


@router.delete("/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wallet(wallet_id: int, db: Session = Depends(get_db)):
    wallet = _get_or_404(db, wallet_id)
    db.delete(wallet)
    db.commit()
    return None
