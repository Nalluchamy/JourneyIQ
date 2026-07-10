from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_verification_token
from app.models.user import User


@pytest.mark.asyncio
async def test_email_verification_endpoint(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Register verified user
    user = User(
        email="verify_endpoint@example.com",
        password_hash="pw",
        full_name="Verify Endpoint User",
        role="customer",
        is_verified=False,
    )
    db_session.add(user)
    await db_session.commit()

    # Generate token
    token = create_verification_token(user.email)

    # Call verify route
    response = await client.get(f"/api/v1/auth/verify?token={token}")
    assert response.status_code == 200
    assert response.json()["message"] == "Email verified successfully"

    # Verify status in database
    await db_session.refresh(user)
    assert user.is_verified is True

    # Call verify route again
    response_again = await client.get(f"/api/v1/auth/verify?token={token}")
    assert response_again.status_code == 200
    assert "already verified" in response_again.json()["message"]


@pytest.mark.asyncio
async def test_password_recovery_and_reset_flow(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Register verified user
    user = User(
        email="recovery@example.com",
        password_hash="$2b$12$UnRealHashMockPlaceholderBcryptPaddingJustForTests",
        full_name="Recovery User",
        role="customer",
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    # 1. Forgot password request
    forgot_payload = {"email": "recovery@example.com"}

    # Mock mail sender to capture the link token
    with patch("app.api.endpoints.auth.get_mail_service") as mock_mail_factory:
        mock_mail = mock_mail_factory.return_value
        mock_mail.send_password_reset_email = AsyncMock()
        response = await client.post(
            "/api/v1/auth/forgot-password", json=forgot_payload
        )
        assert response.status_code == 200
        assert "link has been sent" in response.json()["message"]

        # Extract token from mock mail link call args
        mock_mail.send_password_reset_email.assert_called_once()
        args = mock_mail.send_password_reset_email.call_args[0]
        # args[0] is email, args[1] is token
        captured_token = args[1]

    # 2. Reset password using captured token
    reset_payload = {"token": captured_token, "new_password": "NewStrongPassword123!"}
    reset_res = await client.post("/api/v1/auth/reset-password", json=reset_payload)
    assert reset_res.status_code == 200
    assert "reset successfully" in reset_res.json()["message"]

    # Verify password updated in DB
    await db_session.refresh(user)
    # Check verify password
    from app.core.security import verify_password

    assert verify_password("NewStrongPassword123!", user.password_hash) is True

    # 3. Attempt to reuse the token (should be blocked by checksum invalidation)
    reuse_res = await client.post("/api/v1/auth/reset-password", json=reset_payload)
    assert reuse_res.status_code == 400
    assert "invalid or expired" in reuse_res.json()["message"].lower()
