from decimal import Decimal
from pydantic import BaseModel, Field, model_validator


class GradeInput(BaseModel):
    assignment_id: int = Field(gt=0)
    student_id: int = Field(gt=0)
    points_earned: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    points_possible: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    feedback: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def valid_points(self):
        if self.points_earned > self.points_possible:
            raise ValueError("Points earned cannot exceed points possible")
        return self
