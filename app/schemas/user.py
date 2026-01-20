from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "student@endowal.app",
                    "name": "Avery Park",
                    "role": "student",
                    "is_active": True,
                }
            ]
        }
    )

    email: EmailStr
    name: str | None = None
    role: str = "student"
    is_active: bool = True


class UserCreate(UserBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "teacher@endowal.app",
                    "name": "Morgan Reese",
                    "role": "teacher",
                    "is_active": True,
                    "password": "Teacher123!",
                }
            ]
        }
    )

    password: str


class UserUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"name": "Avery Park", "is_active": True}
            ]
        }
    )

    email: EmailStr | None = None
    name: str | None = None
    role: str | None = None
    is_active: bool | None = None


class UserOut(UserBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 12,
                    "email": "student@endowal.app",
                    "name": "Avery Park",
                    "role": "student",
                    "is_active": True,
                }
            ]
        },
    )

    id: int
