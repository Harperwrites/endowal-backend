from pydantic import BaseModel, ConfigDict


class ClassroomBase(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "teacher_id": 2,
                    "name": "Personal Finance 101",
                    "school_name": "Endowal Academy",
                    "grade_level": "8th",
                }
            ]
        }
    )

    teacher_id: int
    name: str
    school_name: str | None = None
    grade_level: str | None = None


class ClassroomCreate(ClassroomBase):
    model_config = ClassroomBase.model_config


class ClassroomUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"name": "Personal Finance 101 - Period 2", "grade_level": "8th"}
            ]
        }
    )

    teacher_id: int | None = None
    name: str | None = None
    school_name: str | None = None
    grade_level: str | None = None


class ClassroomOut(ClassroomBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "teacher_id": 2,
                    "name": "Personal Finance 101",
                    "school_name": "Endowal Academy",
                    "grade_level": "8th",
                }
            ]
        },
    )

    id: int
