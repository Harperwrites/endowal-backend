from pydantic_settings import BaseSettings
from pydantic import Field, model_validator


class Settings(BaseSettings):
    client_id: str = Field(default="endowal", pattern=r"^[a-z0-9][a-z0-9-]{0,79}$")
    licensee_id: str = "endowal"
    license_id: str = "development"
    parent_license_id: str | None = None
    deployment_environment: str = "development"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    allow_self_registration: bool = True
    credit_enabled: bool = True
    messaging_enabled: bool = True
    interest_enabled: bool = True
    session_cookie_path: str | None = None
    @model_validator(mode="after")
    def production_identity(self):
        if self.deployment_environment == "production":
            if len(self.secret_key) < 32 or self.secret_key == "change-me":
                raise ValueError("Production requires a unique SECRET_KEY of at least 32 characters")
            if self.license_id == "development":
                raise ValueError("Set a client LICENSE_ID before production use")
            if not self.cors_origins or any(not value.startswith("https://") for value in self.cors_origins):
                raise ValueError("Production CORS_ORIGINS must contain explicit HTTPS origins")
        return self

    database_url: str = "sqlite:///./endowal.db"
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
