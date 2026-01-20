from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import WalletBucket
from app.schemas.wallet import WalletBucketCreate, WalletBucketOut, WalletBucketUpdate

router = APIRouter(prefix="/buckets", tags=["wallet-buckets"])


def _get_or_404(db: Session, bucket_id: int) -> WalletBucket:
    bucket = db.get(WalletBucket, bucket_id)
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    return bucket


@router.get("", response_model=list[WalletBucketOut])
def list_buckets(
    skip: int = 0,
    limit: int = 100,
    wallet_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(WalletBucket)
    if wallet_id is not None:
        query = query.filter(WalletBucket.wallet_id == wallet_id)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=WalletBucketOut, status_code=status.HTTP_201_CREATED)
def create_bucket(payload: WalletBucketCreate, db: Session = Depends(get_db)):
    bucket = WalletBucket(**payload.model_dump())
    db.add(bucket)
    db.commit()
    db.refresh(bucket)
    return bucket


@router.get("/{bucket_id}", response_model=WalletBucketOut)
def get_bucket(bucket_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, bucket_id)


@router.patch("/{bucket_id}", response_model=WalletBucketOut)
def update_bucket(
    bucket_id: int, payload: WalletBucketUpdate, db: Session = Depends(get_db)
):
    bucket = _get_or_404(db, bucket_id)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(bucket, key, value)
    db.commit()
    db.refresh(bucket)
    return bucket


@router.delete("/{bucket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bucket(bucket_id: int, db: Session = Depends(get_db)):
    bucket = _get_or_404(db, bucket_id)
    db.delete(bucket)
    db.commit()
    return None
