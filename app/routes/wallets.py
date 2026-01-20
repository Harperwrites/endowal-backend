from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_roles
from app.models import Classroom, StudentWallet, User
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


def _ensure_classroom_access(db: Session, classroom_id: int, current_user: User) -> None:
    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    if current_user.role == "teacher" and classroom.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")


def _ensure_wallet_access(db: Session, wallet: StudentWallet, current_user: User) -> None:
    if current_user.role == "student" and wallet.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "teacher":
        _ensure_classroom_access(db, wallet.classroom_id, current_user)


@router.get("", response_model=list[StudentWalletOut])
def list_wallets(
    skip: int = 0,
    limit: int = 100,
    classroom_id: int | None = None,
    student_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(StudentWallet)
    if current_user.role == "student":
        if student_id is not None and student_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        student_id = current_user.id
    if current_user.role == "teacher":
        if classroom_id is not None:
            _ensure_classroom_access(db, classroom_id, current_user)
            query = query.filter(StudentWallet.classroom_id == classroom_id)
        else:
            query = query.join(
                Classroom, StudentWallet.classroom_id == Classroom.id
            ).filter(Classroom.teacher_id == current_user.id)
    if classroom_id is not None:
        query = query.filter(StudentWallet.classroom_id == classroom_id)
    if student_id is not None:
        query = query.filter(StudentWallet.student_id == student_id)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=StudentWalletOut, status_code=status.HTTP_201_CREATED)
def create_wallet(
    payload: StudentWalletCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    if current_user.role == "teacher":
        _ensure_classroom_access(db, payload.classroom_id, current_user)
    wallet = StudentWallet(**payload.model_dump())
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet


@router.get("/{wallet_id}", response_model=StudentWalletOut)
def get_wallet(
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = _get_or_404(db, wallet_id)
    _ensure_wallet_access(db, wallet, current_user)
    return wallet


@router.patch("/{wallet_id}", response_model=StudentWalletOut)
def update_wallet(
    wallet_id: int,
    payload: StudentWalletUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    wallet = _get_or_404(db, wallet_id)
    _ensure_wallet_access(db, wallet, current_user)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(wallet, key, value)
    db.commit()
    db.refresh(wallet)
    return wallet


@router.delete("/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wallet(
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    wallet = _get_or_404(db, wallet_id)
    _ensure_wallet_access(db, wallet, current_user)
    db.delete(wallet)
    db.commit()
    return None
