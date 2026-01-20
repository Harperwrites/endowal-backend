from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_roles
from app.models import Classroom, StudentWallet, User, WalletBucket
from app.schemas.wallet import WalletBucketCreate, WalletBucketOut, WalletBucketUpdate

router = APIRouter(prefix="/buckets", tags=["wallet-buckets"])


def _get_or_404(db: Session, bucket_id: int) -> WalletBucket:
    bucket = db.get(WalletBucket, bucket_id)
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    return bucket


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


def _get_wallet_or_404(db: Session, wallet_id: int) -> StudentWallet:
    wallet = db.get(StudentWallet, wallet_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet


@router.get("", response_model=list[WalletBucketOut])
def list_buckets(
    skip: int = 0,
    limit: int = 100,
    wallet_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(WalletBucket)
    if current_user.role in ("student", "teacher"):
        query = query.join(
            StudentWallet, WalletBucket.wallet_id == StudentWallet.id
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
        query = query.filter(WalletBucket.wallet_id == wallet_id)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=WalletBucketOut, status_code=status.HTTP_201_CREATED)
def create_bucket(
    payload: WalletBucketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = _get_wallet_or_404(db, payload.wallet_id)
    _ensure_wallet_access(db, wallet, current_user)
    bucket = WalletBucket(**payload.model_dump())
    db.add(bucket)
    db.commit()
    db.refresh(bucket)
    return bucket


@router.get("/{bucket_id}", response_model=WalletBucketOut)
def get_bucket(
    bucket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bucket = _get_or_404(db, bucket_id)
    wallet = _get_wallet_or_404(db, bucket.wallet_id)
    _ensure_wallet_access(db, wallet, current_user)
    return bucket


@router.patch("/{bucket_id}", response_model=WalletBucketOut)
def update_bucket(
    bucket_id: int,
    payload: WalletBucketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bucket = _get_or_404(db, bucket_id)
    wallet = _get_wallet_or_404(db, bucket.wallet_id)
    _ensure_wallet_access(db, wallet, current_user)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(bucket, key, value)
    db.commit()
    db.refresh(bucket)
    return bucket


@router.delete("/{bucket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bucket(
    bucket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bucket = _get_or_404(db, bucket_id)
    wallet = _get_wallet_or_404(db, bucket.wallet_id)
    _ensure_wallet_access(db, wallet, current_user)
    db.delete(bucket)
    db.commit()
    return None
