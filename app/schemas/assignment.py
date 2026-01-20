import datetime as dt
from pydantic import BaseModel, ConfigDict


class AssignmentBase(BaseModel):
    classroom_id: int
    created_by: int
    title: str
    description: str | None = None
    category: str | None = None
    target_amount: float | None = None
    due_date: dt.date | None = None
    status: str = "draft"


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    target_amount: float | None = None
    due_date: dt.date | None = None
    status: str | None = None


class AssignmentOut(AssignmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
