from pydantic import BaseModel, ConfigDict


class StudentWalletBase(BaseModel):
    classroom_id: int
    student_id: int
    balance: float = 0


class StudentWalletCreate(StudentWalletBase):
    pass


class StudentWalletUpdate(BaseModel):
    classroom_id: int | None = None
    student_id: int | None = None
    balance: float | None = None


class StudentWalletOut(StudentWalletBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class WalletBucketBase(BaseModel):
    wallet_id: int
    name: str
    percent_target: float | None = None


class WalletBucketCreate(WalletBucketBase):
    pass


class WalletBucketUpdate(BaseModel):
    name: str | None = None
    percent_target: float | None = None


class WalletBucketOut(WalletBucketBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
