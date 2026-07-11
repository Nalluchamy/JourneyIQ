import os

from pydantic_settings import BaseSettings, SettingsConfigDict

env = os.getenv("ENVIRONMENT", "development").lower()
env_files = [".env"]
if env != "development":
    env_files.insert(0, f".env.{env}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=tuple(env_files), env_file_encoding="utf-8", extra="ignore"
    )

    # Project Info
    PROJECT_NAME: str = "JourneyIQ"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/journeyiq"

    # Security
    SECRET_KEY: str = "replace-with-a-very-secure-secret-key-for-production"
    JWT_SECRET: str = "replace-with-a-very-secure-jwt-secret-for-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REQUIRE_EMAIL_VERIFICATION: bool = True

    # URLs
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"

    # Redis Caching (Optional)
    REDIS_URL: str | None = None


settings = Settings()
