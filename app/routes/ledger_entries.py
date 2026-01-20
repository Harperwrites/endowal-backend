from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_roles
from app.models import Classroom, LedgerEntry, StudentWallet, User
from app.schemas.ledger import LedgerEntryCreate, LedgerEntryOut, LedgerEntryUpdate

router = APIRouter(prefix="/ledger-entries", tags=["ledger-entries"])


def _get_or_404(db: Session, entry_id: int) -> LedgerEntry:
    entry = db.get(LedgerEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Ledger entry not found")
    return entry


def _ensure_classroom_access(db: Session, classroom_id: int, current_user: User) -> None:
    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    if current_user.role == "teacher" and classroom.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")


def _get_wallet_or_404(db: Session, wallet_id: int) -> StudentWallet:
    wallet = db.get(StudentWallet, wallet_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet


def _ensure_wallet_access(db: Session, wallet: StudentWallet, current_user: User) -> None:
    if current_user.role == "student" and wallet.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "teacher":
        _ensure_classroom_access(db, wallet.classroom_id, current_user)


@router.get("", response_model=list[LedgerEntryOut])
def list_ledger_entries(
    skip: int = 0,
    limit: int = 100,
    wallet_id: int | None = None,
    assignment_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(LedgerEntry)
    if current_user.role in ("student", "teacher"):
        query = query.join(
            StudentWallet, LedgerEntry.wallet_id == StudentWallet.id
        )
        if current_user.role == "student":
            query = query.filter(StudentWallet.student_id == current_user.id)
        if current_user.role == "teacher":
            query = query.join(
                Classroom, StudentWallet.classroom_id == Classroom.id
            ).filter(Classroom.teacher_id == current_user.id)
    if wallet_id is not None:
        wallet = _get_wallet_or_404(db, wallet_id)
        _ensure_wallet_access(db, wallet, current_user)
        query = query.filter(LedgerEntry.wallet_id == wallet_id)
    if assignment_id is not None:
        query = query.filter(LedgerEntry.assignment_id == assignment_id)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=LedgerEntryOut, status_code=status.HTTP_201_CREATED)
def create_ledger_entry(
    payload: LedgerEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    wallet = _get_wallet_or_404(db, payload.wallet_id)
    _ensure_wallet_access(db, wallet, current_user)
    entry = LedgerEntry(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{entry_id}", response_model=LedgerEntryOut)
def get_ledger_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = _get_or_404(db, entry_id)
    wallet = _get_wallet_or_404(db, entry.wallet_id)
    _ensure_wallet_access(db, wallet, current_user)
    return entry


@router.patch("/{entry_id}", response_model=LedgerEntryOut)
def update_ledger_entry(
    entry_id: int,
    payload: LedgerEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    entry = _get_or_404(db, entry_id)
    wallet = _get_wallet_or_404(db, entry.wallet_id)
    _ensure_wallet_access(db, wallet, current_user)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ledger_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "admin")),
):
    entry = _get_or_404(db, entry_id)
    wallet = _get_wallet_or_404(db, entry.wallet_id)
    _ensure_wallet_access(db, wallet, current_user)
    db.delete(entry)
    db.commit()
    return None
