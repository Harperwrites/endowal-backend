from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import LedgerEntry
from app.schemas.ledger import LedgerEntryCreate, LedgerEntryOut, LedgerEntryUpdate

router = APIRouter(prefix="/ledger-entries", tags=["ledger-entries"])


def _get_or_404(db: Session, entry_id: int) -> LedgerEntry:
    entry = db.get(LedgerEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Ledger entry not found")
    return entry


@router.get("", response_model=list[LedgerEntryOut])
def list_ledger_entries(
    skip: int = 0,
    limit: int = 100,
    wallet_id: int | None = None,
    assignment_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(LedgerEntry)
    if wallet_id is not None:
        query = query.filter(LedgerEntry.wallet_id == wallet_id)
    if assignment_id is not None:
        query = query.filter(LedgerEntry.assignment_id == assignment_id)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=LedgerEntryOut, status_code=status.HTTP_201_CREATED)
def create_ledger_entry(payload: LedgerEntryCreate, db: Session = Depends(get_db)):
    entry = LedgerEntry(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{entry_id}", response_model=LedgerEntryOut)
def get_ledger_entry(entry_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, entry_id)


@router.patch("/{entry_id}", response_model=LedgerEntryOut)
def update_ledger_entry(
    entry_id: int, payload: LedgerEntryUpdate, db: Session = Depends(get_db)
):
    entry = _get_or_404(db, entry_id)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ledger_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = _get_or_404(db, entry_id)
    db.delete(entry)
    db.commit()
    return None
