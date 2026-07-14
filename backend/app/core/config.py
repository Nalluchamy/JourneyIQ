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
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/journeyiq"

    # Security
    SECRET_KEY: str = "replace-with-a-very-secure-secret-key-for-production"
    JWT_SECRET: str = "replace-with-a-very-secure-jwt-secret-for-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REQUIRE_EMAIL_VERIFICATION: bool = False

    # URLs
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"

    # Redis Caching (Optional)
    REDIS_URL: str | None = None

    # AI / LLM Integrations
    NVIDIA_API_KEY: str | None = None

    # Supabase Integration
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None

    @classmethod
    def validate_production_secrets(cls, values: "Settings") -> "Settings":
        if values.ENVIRONMENT.lower() in ("production", "prod", "staging"):
            sec_placeholder = "replace-with-a-very-secure-secret-key-for-production"
            jwt_placeholder = "replace-with-a-very-secure-jwt-secret-for-production"
            if values.SECRET_KEY == sec_placeholder or sec_placeholder in values.SECRET_KEY:
                raise ValueError("SECRET_KEY must be overridden with a secure random key in production/staging environments.")
            if values.JWT_SECRET == jwt_placeholder or jwt_placeholder in values.JWT_SECRET:
                raise ValueError("JWT_SECRET must be overridden with a secure random key in production/staging environments.")
            if not values.SUPABASE_URL:
                raise ValueError("SUPABASE_URL must be specified in production/staging environments.")
            if not values.SUPABASE_KEY:
                raise ValueError("SUPABASE_KEY must be specified in production/staging environments.")
        return values

    def __init__(self, **values):
        super().__init__(**values)
        self.validate_production_secrets(self)


settings = Settings()

