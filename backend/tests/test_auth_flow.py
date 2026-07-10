import datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password, hash_token
from app.models.user import User
from app.models.refresh_token import RefreshToken


@pytest.mark.asyncio
async def test_user_registration_flow(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # 1. Register a new user
    register_data = {
        "email": "register_test@example.com",
        "password": "StrongPassword123!",
        "full_name": "New Test User",
        "phone": "+1234567890",
    }

    # Patch mock email service during registration
    with patch("app.api.endpoints.auth.get_mail_service") as mock_mail_factory:
        mock_mail = mock_mail_factory.return_value
        mock_mail.send_verification_email = AsyncMock()
        response = await client.post("/api/v1/auth/register", json=register_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "register_test@example.com"
        assert "password" not in data  # Never return raw password

        # Verify mock mail was called
        mock_mail.send_verification_email.assert_called_once()

    # 2. Query user in DB and assert fields
    stmt = select(User).where(User.email == "register_test@example.com")
    res = await db_session.execute(stmt)
    db_user = res.scalar_one_or_none()
    assert db_user is not None
    assert db_user.is_verified is False
    assert verify_password("StrongPassword123!", db_user.password_hash) is True


@pytest.mark.asyncio
async def test_login_and_verification_requirement(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Register and save unverified user
    user = User(
        email="unverified@example.com",
        password_hash="$2b$12$UnRealHashMockPlaceholderBcryptPaddingJustForTests",
        full_name="Unverified User",
        role="customer",
        is_verified=False,
    )
    db_session.add(user)
    await db_session.commit()

    # Attempt login (should be blocked by verification check)
    login_data = {
        "username": "unverified@example.com",
        "password": "Password123",
    }
    with patch("app.api.endpoints.auth.verify_password", return_value=True):
        login_res = await client.post("/api/v1/auth/login", data=login_data)
        assert login_res.status_code == 400
        assert "verification required" in login_res.json()["message"].lower()

    # Verify user
    user.is_verified = True
    await db_session.commit()

    # Login should succeed now
    with patch("app.api.endpoints.auth.verify_password", return_value=True):
        login_res = await client.post("/api/v1/auth/login", data=login_data)
        assert login_res.status_code == 200
        tokens = login_res.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens


@pytest.mark.asyncio
async def test_account_lockout_after_failures(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Register verified user
    user = User(
        email="lockout@example.com",
        password_hash="$2b$12$UnRealHashMockPlaceholderBcryptPaddingJustForTests",
        full_name="Lockout User",
        role="customer",
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    login_data = {"username": "lockout@example.com", "password": "WrongPassword"}

    # Simulate 4 failed logins returning 400
    for i in range(4):
        res = await client.post("/api/v1/auth/login", data=login_data)
        assert res.status_code == 400

    # 5th attempt triggers lockout and returns 403
    trigger_res = await client.post("/api/v1/auth/login", data=login_data)
    assert trigger_res.status_code == 403
    assert "locked" in trigger_res.json()["message"].lower()

    # 6th attempt returns 403 Forbidden due to active account lockout
    lock_res = await client.post("/api/v1/auth/login", data=login_data)
    assert lock_res.status_code == 403
    assert "locked" in lock_res.json()["message"].lower()

    # Verify locked fields in DB
    await db_session.refresh(user)
    assert user.locked_until is not None
    assert user.failed_login_attempts == 0  # Cleared after lockout triggers


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_revocation(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Register verified user
    user = User(
        email="refresh@example.com",
        password_hash="$2b$12$UnRealHashMockPlaceholderBcryptPaddingJustForTests",
        full_name="Refresh User",
        role="customer",
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Simulate successful login to get tokens
    login_data = {"username": "refresh@example.com", "password": "CorrectPassword"}
    with patch("app.api.endpoints.auth.verify_password", return_value=True):
        login_res = await client.post("/api/v1/auth/login", data=login_data)
        tokens = login_res.json()
        refresh_token = tokens["refresh_token"]

    # 1. Perform token refresh
    refresh_res = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert "access_token" in new_tokens
    new_refresh = new_tokens["refresh_token"]

    # 2. Check DB status: old token should be marked revoked, new token active
    old_hash = hash_token(refresh_token)
    new_hash = hash_token(new_refresh)

    stmt_old = select(RefreshToken).where(RefreshToken.token_hash == old_hash)
    db_old = (await db_session.execute(stmt_old)).scalar_one_or_none()
    assert db_old is not None
    assert db_old.is_revoked is True

    stmt_new = select(RefreshToken).where(RefreshToken.token_hash == new_hash)
    db_new = (await db_session.execute(stmt_new)).scalar_one_or_none()
    assert db_new is not None
    assert db_new.is_revoked is False

    # 3. Attempting to refresh again with the old revoked token should fail (replay attack guard)
    replay_res = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert replay_res.status_code == 401


@pytest.mark.asyncio
async def test_logout_revocation(client: AsyncClient, db_session: AsyncSession) -> None:
    user = User(
        email="logout_test@example.com",
        password_hash="$2b$12$UnRealHashMockPlaceholderBcryptPaddingJustForTests",
        full_name="Logout User",
        role="customer",
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    login_data = {"username": "logout_test@example.com", "password": "Password"}
    with patch("app.api.endpoints.auth.verify_password", return_value=True):
        login_res = await client.post("/api/v1/auth/login", data=login_data)
        tokens = login_res.json()
        refresh_token = tokens["refresh_token"]

    # Call logout
    logout_res = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": refresh_token}
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["message"] == "Logged out successfully"

    # Verify old token revoked in DB
    hashed = hash_token(refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == hashed)
    db_token = (await db_session.execute(stmt)).scalar_one_or_none()
    assert db_token is not None
    assert db_token.is_revoked is True
