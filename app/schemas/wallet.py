from pydantic import BaseModel, ConfigDict


class StudentWalletBase(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"classroom_id": 1, "student_id": 7, "balance": 125.0}
            ]
        }
    )

    classroom_id: int
    student_id: int
    balance: float = 0


class StudentWalletCreate(StudentWalletBase):
    model_config = StudentWalletBase.model_config


class StudentWalletUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"balance": 150.0}]}
    )

    classroom_id: int | None = None
    student_id: int | None = None
    balance: float | None = None


class StudentWalletOut(StudentWalletBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 9,
                    "classroom_id": 1,
                    "student_id": 7,
                    "balance": 125.0,
                }
            ]
        },
    )

    id: int


class WalletBucketBase(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"wallet_id": 9, "name": "Giving", "percent_target": 10.0}
            ]
        }
    )

    wallet_id: int
    name: str
    percent_target: float | None = None


class WalletBucketCreate(WalletBucketBase):
    model_config = WalletBucketBase.model_config


class WalletBucketUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"name": "Saving", "percent_target": 60.0}]}
    )

    name: str | None = None
    percent_target: float | None = None


class WalletBucketOut(WalletBucketBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 3,
                    "wallet_id": 9,
                    "name": "Giving",
                    "percent_target": 10.0,
                }
            ]
        },
    )

    id: int
