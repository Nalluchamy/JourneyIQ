from fastapi import FastAPI
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "JourneyIQ ML Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"


settings = Settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="JourneyIQ - Machine Learning Service Skeleton",
)


@app.get("/")
def read_root() -> dict:
    """Default root endpoint for confirmation.

    Returns:
        dict: Status message.
    """
    return {"message": "JourneyIQ ML Service is running"}


@app.get("/health")
def health_check() -> dict:
    """Basic health check for Docker container status checks.

    Returns:
        dict: Health status report.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }
