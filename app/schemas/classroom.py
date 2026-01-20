from pydantic import BaseModel, ConfigDict


class ClassroomBase(BaseModel):
    teacher_id: int
    name: str
    school_name: str | None = None
    grade_level: str | None = None


class ClassroomCreate(ClassroomBase):
    pass


class ClassroomUpdate(BaseModel):
    teacher_id: int | None = None
    name: str | None = None
    school_name: str | None = None
    grade_level: str | None = None


class ClassroomOut(ClassroomBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
