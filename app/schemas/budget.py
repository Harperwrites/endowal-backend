from pydantic import BaseModel, ConfigDict


class BudgetSubmissionBase(BaseModel):
    assignment_id: int
    student_id: int
    total_planned: float
    notes: str | None = None
    status: str = "submitted"


class BudgetSubmissionCreate(BudgetSubmissionBase):
    pass


class BudgetSubmissionUpdate(BaseModel):
    total_planned: float | None = None
    notes: str | None = None
    status: str | None = None


class BudgetSubmissionOut(BudgetSubmissionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class BudgetLineItemBase(BaseModel):
    submission_id: int
    category: str
    amount: float


class BudgetLineItemCreate(BudgetLineItemBase):
    pass


class BudgetLineItemUpdate(BaseModel):
    category: str | None = None
    amount: float | None = None


class BudgetLineItemOut(BudgetLineItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
