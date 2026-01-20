from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./endowal.db"

    class Config:
        env_file = ".env"


settings = Settings()
