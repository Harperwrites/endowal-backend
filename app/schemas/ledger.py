from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


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
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    entry_type: Literal["deposit", "withdrawal"]
    source: Literal["teacher_grant", "student_action"]
    memo: str | None = None


class LedgerEntryCreate(LedgerEntryBase):
    model_config = LedgerEntryBase.model_config


class LedgerEntryUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"memo": "Updated memo"}]}
    )

    assignment_id: int | None = None
    amount: Decimal = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    entry_type: Literal["deposit", "withdrawal"] = None
    source: Literal["teacher_grant", "student_action"] = None
    memo: str | None = None


class LedgerEntryOut(LedgerEntryBase):
    transfer_id: str | None = None
    assignment_title: str | None = None

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
