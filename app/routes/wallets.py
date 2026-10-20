from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, and_

from app.db.session import get_db
from app.deps import get_current_user, require_roles
from app.models import Classroom, StudentWallet, User, LedgerEntry, Assignment, Enrollment
from app.core.accounting import lock_wallet, check_balance, signed
from decimal import Decimal
from uuid import uuid4, UUID
from typing import Literal
from app.schemas.ledger import LedgerEntryOut
from pydantic import BaseModel, Field
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
    wallet = StudentWallet(**payload.model_dump(exclude={"balance"}))
    db.add(wallet)
    db.flush()
    if payload.balance:
        db.add(LedgerEntry(wallet_id=wallet.id, amount=payload.balance, entry_type="deposit", source="teacher_grant", memo="Opening balance"))
    db.commit()
    db.refresh(wallet)
    return wallet


class TransferRequest(BaseModel):
    from_wallet_id: int
    to_wallet_id: int
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    memo: str | None = Field(default=None, max_length=255)


@router.post("/transfer")
def transfer(payload: TransferRequest, db: Session = Depends(get_db),
             current_user: User = Depends(require_roles("teacher", "admin"))):
    if payload.from_wallet_id == payload.to_wallet_id:
        raise HTTPException(400, "Choose two different wallets")
    # Stable lock order prevents opposite-direction transfers from deadlocking.
    locked = {key: lock_wallet(db, key) for key in sorted([payload.from_wallet_id, payload.to_wallet_id])}
    sender, recipient = locked[payload.from_wallet_id], locked[payload.to_wallet_id]
    _ensure_wallet_access(db, sender, current_user)
    _ensure_wallet_access(db, recipient, current_user)
    if sender.classroom_id != recipient.classroom_id:
        raise HTTPException(400, "Transfers must stay within one classroom")
    check_balance(sender, -payload.amount)
    check_balance(recipient, payload.amount)
    transfer_id = str(uuid4())
    for wallet, kind in [(sender, "withdrawal"), (recipient, "deposit")]:
        db.add(LedgerEntry(wallet_id=wallet.id, amount=payload.amount, entry_type=kind,
                           source="teacher_grant", transfer_id=transfer_id, memo=payload.memo or "Classroom transfer"))
    db.commit()
    return {"status": "completed"}


@router.get("/overview")
def account_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.schemas.ledger import LedgerEntryOut
    # Totals and recent entries come from a single SQL statement/snapshot.
    recent = select(LedgerEntry, func.row_number().over(
        partition_by=LedgerEntry.wallet_id, order_by=LedgerEntry.id.desc()
    ).label("position")).subquery()
    entry = aliased(LedgerEntry, recent)
    query = db.query(StudentWallet, entry, Classroom.name).join(Classroom, Classroom.id == StudentWallet.classroom_id).outerjoin(recent, and_(
        recent.c.wallet_id == StudentWallet.id, recent.c.position <= 10
    ))
    if current_user.role == "student":
        query = query.filter(StudentWallet.student_id == current_user.id)
    elif current_user.role == "teacher":
        query = query.filter(Classroom.teacher_id == current_user.id)
    accounts = {}
    for wallet, activity, classroom_name in query.order_by(StudentWallet.id, recent.c.id.desc()).all():
        if wallet.id not in accounts:
            accounts[wallet.id] = {**StudentWalletOut.model_validate(wallet).model_dump(mode="json"), "classroom_name": classroom_name, "activity": []}
        if activity:
            accounts[wallet.id]["activity"].append(LedgerEntryOut.model_validate(activity).model_dump(mode="json"))
    return list(accounts.values())


def student_account_access(db, wallet, user):
    _ensure_wallet_access(db, wallet, user)
    if user.role == "student" and not db.query(Enrollment).filter_by(
        classroom_id=wallet.classroom_id, student_id=user.id, status="active"
    ).first():
        raise HTTPException(403, "You must be actively enrolled in this classroom")


@router.get("/{wallet_id}/assignments")
def wallet_assignments(wallet_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    wallet = _get_or_404(db, wallet_id)
    student_account_access(db, wallet, user)
    assignments = db.query(Assignment).filter_by(classroom_id=wallet.classroom_id)
    if user.role == "student": assignments = assignments.filter(Assignment.status != "draft")
    return [{"id": a.id, "title": a.title, "status": a.status,
             "description": a.description, "due_date": str(a.due_date) if a.due_date else None}
            for a in assignments.order_by(Assignment.id).all()]


class StudentTransaction(BaseModel):
    assignment_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    entry_type: Literal["deposit", "withdrawal"]
    memo: str = Field(min_length=1, max_length=255)
    request_id: UUID


@router.post("/{wallet_id}/transactions", response_model=LedgerEntryOut, status_code=201)
def student_transaction(wallet_id: int, payload: StudentTransaction,
                        db: Session = Depends(get_db), user: User = Depends(require_roles("student"))):
    wallet = _get_or_404(db, wallet_id)
    student_account_access(db, wallet, user)
    assignment = db.get(Assignment, payload.assignment_id)
    if not assignment or assignment.classroom_id != wallet.classroom_id:
        raise HTTPException(400, "Choose an assignment from this account’s classroom")
    memo = payload.memo.strip()
    if not memo: raise HTTPException(422, "Describe this deposit or expense")
    wallet = lock_wallet(db, wallet.id)
    existing = db.query(LedgerEntry).filter_by(client_request_id=str(payload.request_id)).first()
    if existing:
        if (existing.wallet_id, existing.assignment_id, existing.amount, existing.entry_type, existing.memo) != (wallet.id, assignment.id, payload.amount, payload.entry_type, memo):
            raise HTTPException(409, "This request was already used for a different transaction")
        return existing
    if assignment.status not in ("active", "published"):
        raise HTTPException(400, "This assignment is not open for banking activity")
    check_balance(wallet, signed(payload.amount, payload.entry_type))
    entry = LedgerEntry(wallet_id=wallet.id, assignment_id=assignment.id, amount=payload.amount,
                        entry_type=payload.entry_type, source="student_action", memo=memo,
                        client_request_id=str(payload.request_id))
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


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
    if "balance" in updates:
        raise HTTPException(400, "Record a deposit or withdrawal to change the balance")
    if current_user.role == "teacher" and "classroom_id" in updates:
        _ensure_classroom_access(db, updates["classroom_id"], current_user)
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
    if db.query(LedgerEntry).filter(LedgerEntry.wallet_id == wallet.id).first():
        raise HTTPException(400, "Accounts with transaction history cannot be deleted")
    db.delete(wallet)
    db.commit()
    return None
