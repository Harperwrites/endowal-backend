import datetime as dt
from pydantic import BaseModel, ConfigDict


class AssignmentBase(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "classroom_id": 1,
                    "created_by": 2,
                    "title": "Budget a School Event",
                    "description": "Plan costs for a class fundraiser.",
                    "category": "budgeting",
                    "target_amount": 500.0,
                    "due_date": "2026-03-15",
                    "status": "published",
                }
            ]
        }
    )

    classroom_id: int
    created_by: int
    title: str
    description: str | None = None
    category: str | None = None
    target_amount: float | None = None
    due_date: dt.date | None = None
    status: str = "draft"


class AssignmentCreate(AssignmentBase):
    model_config = AssignmentBase.model_config


class AssignmentUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"status": "published", "due_date": "2026-03-15"}
            ]
        }
    )

    title: str | None = None
    description: str | None = None
    category: str | None = None
    target_amount: float | None = None
    due_date: dt.date | None = None
    status: str | None = None


class AssignmentOut(AssignmentBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 4,
                    "classroom_id": 1,
                    "created_by": 2,
                    "title": "Budget a School Event",
                    "description": "Plan costs for a class fundraiser.",
                    "category": "budgeting",
                    "target_amount": 500.0,
                    "due_date": "2026-03-15",
                    "status": "published",
                }
            ]
        },
    )

    id: int
