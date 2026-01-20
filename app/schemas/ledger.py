from pydantic import BaseModel, ConfigDict


class LedgerEntryBase(BaseModel):
    wallet_id: int
    assignment_id: int | None = None
    amount: float
    entry_type: str
    source: str
    memo: str | None = None


class LedgerEntryCreate(LedgerEntryBase):
    pass


class LedgerEntryUpdate(BaseModel):
    assignment_id: int | None = None
    amount: float | None = None
    entry_type: str | None = None
    source: str | None = None
    memo: str | None = None


class LedgerEntryOut(LedgerEntryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
