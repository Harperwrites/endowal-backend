from pydantic import BaseModel, ConfigDict


class EnrollmentBase(BaseModel):
    classroom_id: int
    student_id: int
    status: str = "active"


class EnrollmentCreate(EnrollmentBase):
    pass


class EnrollmentUpdate(BaseModel):
    status: str | None = None


class EnrollmentOut(EnrollmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
