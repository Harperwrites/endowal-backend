from pydantic import BaseModel, ConfigDict


class LedgerEntryBase(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "wallet_id": 9,
                    "assignment_id": 4,
                    "amount": 25.0,
                    "entry_type": "deposit",
                    "source": "teacher_grant",
                    "memo": "Weekly savings bonus",
                }
            ]
        }
    )

    wallet_id: int
    assignment_id: int | None = None
    amount: float
    entry_type: str
    source: str
    memo: str | None = None


class LedgerEntryCreate(LedgerEntryBase):
    model_config = LedgerEntryBase.model_config


class LedgerEntryUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"memo": "Updated memo"}]}
    )

    assignment_id: int | None = None
    amount: float | None = None
    entry_type: str | None = None
    source: str | None = None
    memo: str | None = None


class LedgerEntryOut(LedgerEntryBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 14,
                    "wallet_id": 9,
                    "assignment_id": 4,
                    "amount": 25.0,
                    "entry_type": "deposit",
                    "source": "teacher_grant",
                    "memo": "Weekly savings bonus",
                }
            ]
        },
    )

    id: int
