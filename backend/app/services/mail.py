from abc import ABC, abstractmethod

import structlog

from app.core.config import settings

logger = structlog.get_logger("auth_mail")


class BaseMailService(ABC):
    """Abstract interface for all mail delivery providers."""

    @abstractmethod
    async def send_verification_email(self, email: str, token: str) -> None:
        """Send account verification token to user's email address."""
        pass

    @abstractmethod
    async def send_password_reset_email(self, email: str, token: str) -> None:
        """Send password reset token to user's email address."""
        pass


class MockMailService(BaseMailService):
    """Mock mail service logging links to terminal output and structlog."""

    async def send_verification_email(self, email: str, token: str) -> None:
        verify_url = (
            f"{settings.BACKEND_URL}{settings.API_V1_STR}/auth/verify?token={token}"
        )
        logger.info(
            "MOCK_MAIL: Sending account verification", to=email, link=verify_url
        )
        print(
            f"\n--- [MOCK MAIL SENDER] ---\n"
            f"To: {email}\n"
            f"Subject: Verify your JourneyIQ Account\n"
            f"Link: {verify_url}\n"
            f"---------------------------\n"
        )

    async def send_password_reset_email(self, email: str, token: str) -> None:
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        logger.info("MOCK_MAIL: Sending password reset", to=email, link=reset_url)
        print(
            f"\n--- [MOCK MAIL SENDER] ---\n"
            f"To: {email}\n"
            f"Subject: Reset your JourneyIQ Password\n"
            f"Link: {reset_url}\n"
            f"---------------------------\n"
        )


def get_mail_service() -> BaseMailService:
    """Dependency injection factory for mail service providers."""
    # Instantiating custom SendGrid/Resend/SMTP services based on config can go here
    return MockMailService()
