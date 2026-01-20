from pydantic import BaseModel, ConfigDict


class BudgetSubmissionBase(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "assignment_id": 4,
                    "student_id": 7,
                    "total_planned": 120.0,
                    "notes": "Keeping costs lean.",
                    "status": "submitted",
                }
            ]
        }
    )

    assignment_id: int
    student_id: int
    total_planned: float
    notes: str | None = None
    status: str = "submitted"


class BudgetSubmissionCreate(BudgetSubmissionBase):
    model_config = BudgetSubmissionBase.model_config


class BudgetSubmissionUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"status": "approved"}]}
    )

    total_planned: float | None = None
    notes: str | None = None
    status: str | None = None


class BudgetSubmissionOut(BudgetSubmissionBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 6,
                    "assignment_id": 4,
                    "student_id": 7,
                    "total_planned": 120.0,
                    "notes": "Keeping costs lean.",
                    "status": "submitted",
                }
            ]
        },
    )

    id: int


class BudgetLineItemBase(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"submission_id": 6, "category": "Supplies", "amount": 45.0}
            ]
        }
    )

    submission_id: int
    category: str
    amount: float


class BudgetLineItemCreate(BudgetLineItemBase):
    model_config = BudgetLineItemBase.model_config


class BudgetLineItemUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"amount": 50.0}]}
    )

    category: str | None = None
    amount: float | None = None


class BudgetLineItemOut(BudgetLineItemBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 11,
                    "submission_id": 6,
                    "category": "Supplies",
                    "amount": 45.0,
                }
            ]
        },
    )

    id: int
