from pydantic import BaseModel, ConfigDict


class EnrollmentBase(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"classroom_id": 1, "student_id": 7, "status": "active"}
            ]
        }
    )

    classroom_id: int
    student_id: int
    status: str = "active"


class EnrollmentCreate(EnrollmentBase):
    model_config = EnrollmentBase.model_config


class EnrollmentUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"status": "inactive"}]}
    )

    status: str | None = None


class EnrollmentOut(EnrollmentBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 3,
                    "classroom_id": 1,
                    "student_id": 7,
                    "status": "active",
                }
            ]
        },
    )

    id: int
