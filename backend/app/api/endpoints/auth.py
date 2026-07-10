import datetime
import hashlib
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rate_limiter import InMemoryRateLimiter
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    create_verification_token,
    decode_token,
    get_password_hash,
    hash_token,
    verify_password,
)
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserRegister,
)
from app.api.deps import get_current_user
from app.schemas.user import UserRead
from app.services.mail import get_mail_service
from app.utils.event_logger import log_event

router = APIRouter()

# Instantiate rate limiters: 5 requests per minute per IP
login_limiter = InMemoryRateLimiter(requests_limit=5, window_seconds=60)
register_limiter = InMemoryRateLimiter(requests_limit=5, window_seconds=60)


async def log_security_event(
    db: AsyncSession,
    user_id: int | None,
    event_type: str,
    request: Request,
    details: dict[str, Any] | None = None,
) -> None:
    """Create a security audit log entry."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    audit = AuditLog(
        user_id=user_id,
        event_type=event_type,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details,
    )
    db.add(audit)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(register_limiter)],
)
async def register(
    request: Request,
    user_in: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Register a new customer account, auto-verify, and return login tokens."""
    # Check if duplicate email exists
    email_check = await db.execute(select(User).where(User.email == user_in.email))
    if email_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    # Hash password and store user (auto-verified for seamless onboarding)
    hashed_pw = get_password_hash(user_in.password)
    user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        password_hash=hashed_pw,
        phone=user_in.phone,
        role="customer",
        is_verified=True,
    )
    db.add(user)
    await db.flush()  # Resolve user.id

    # Log registration audit event
    await log_security_event(
        db,
        user.id,
        "registration_completed",
        request,
        {"email": user.email},
    )

    # Generate tokens for immediate auto-login
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Hash refresh token before database storage
    hashed_rt = hash_token(refresh_token)
    rt_expires = datetime.datetime.now(datetime.timezone.utc).replace(
        tzinfo=None
    ) + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db_rt = RefreshToken(user_id=user.id, token_hash=hashed_rt, expires_at=rt_expires)
    db.add(db_rt)

    await log_event(db, request, "login", user_id=user.id)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/verify", status_code=status.HTTP_200_OK)
async def verify_email(
    request: Request,
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Verify email verification token and activate user verification flag."""
    invalid_token_exc = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired verification token",
    )
    try:
        payload = decode_token(token)
        email = payload.get("sub")
        token_type = payload.get("type")
        if email is None or token_type != "email_verification":
            raise invalid_token_exc
    except JWTError:
        raise invalid_token_exc

    # Query the user
    user_res = await db.execute(select(User).where(User.email == email))
    user = user_res.scalar_one_or_none()
    if user is None:
        raise invalid_token_exc

    if user.is_verified:
        return {"message": "Email is already verified"}

    user.is_verified = True
    await log_security_event(db, user.id, "email_verified", request)
    await db.commit()

    return {"message": "Email verified successfully"}


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(login_limiter)],
)
async def login(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Any:
    """Login flow checking account status, verified state, lockouts, and credentials."""
    login_failure_exc = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Incorrect email or password",
    )

    # Look up user
    user_res = await db.execute(select(User).where(User.email == form_data.username))
    user = user_res.scalar_one_or_none()

    if user is None:
        # Prevent user enumeration by logging but returning standard generic error
        await log_security_event(
            db,
            None,
            "login_failed_unregistered",
            request,
            {"attempted_email": form_data.username},
        )
        await db.commit()
        raise login_failure_exc

    # Inactive or deleted checks
    if not user.is_active or user.is_deleted:
        await log_security_event(db, user.id, "login_failed_inactive", request)
        await db.commit()
        raise login_failure_exc

    # Lockout check
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    if user.locked_until and user.locked_until > now:
        lock_seconds = int((user.locked_until - now).total_seconds())
        lock_minutes = (lock_seconds // 60) + 1
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is temporarily locked. Try again in {lock_minutes} minutes.",
        )

    # Verify credentials
    if not verify_password(form_data.password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = now + datetime.timedelta(minutes=15)
            user.failed_login_attempts = 0
            await log_security_event(db, user.id, "account_locked", request)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account locked due to too many failed login attempts. Try again in 15 minutes.",
            )
        await log_security_event(db, user.id, "login_failed_password", request)
        await db.commit()
        raise login_failure_exc

    # Check email verification requirements
    if settings.REQUIRE_EMAIL_VERIFICATION and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification required. Please check your inbox.",
        )

    # Success: Clear lockouts and failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None

    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Hash refresh token before database storage
    hashed_rt = hash_token(refresh_token)
    rt_expires = datetime.datetime.now(datetime.timezone.utc).replace(
        tzinfo=None
    ) + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db_rt = RefreshToken(user_id=user.id, token_hash=hashed_rt, expires_at=rt_expires)
    db.add(db_rt)

    await log_security_event(db, user.id, "login_success", request)
    await log_event(db, request, "login", user_id=user.id)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    token_in: TokenRefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Implement Refresh Token Rotation, generating new pairs and revoking used hashes."""
    refresh_failure_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )
    try:
        payload = decode_token(token_in.refresh_token)
        user_id_str = payload.get("sub")
        token_type = payload.get("type")
        if user_id_str is None or token_type != "refresh":
            raise refresh_failure_exc
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise refresh_failure_exc

    # Query active user
    user_res = await db.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()
    if user is None or not user.is_active or user.is_deleted:
        raise refresh_failure_exc

    # Verify hashed token exists in DB and is active
    hashed_rt = hash_token(token_in.refresh_token)
    rt_res = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hashed_rt)
    )
    db_token = rt_res.scalar_one_or_none()

    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    if db_token is None or db_token.is_revoked or db_token.expires_at < now:
        raise refresh_failure_exc

    # Rotate tokens: Revoke old token
    db_token.is_revoked = True

    # Generate new pair
    new_access = create_access_token(user.id)
    new_refresh = create_refresh_token(user.id)

    new_hashed_rt = hash_token(new_refresh)
    new_expires = now + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    new_db_token = RefreshToken(
        user_id=user.id, token_hash=new_hashed_rt, expires_at=new_expires
    )
    db.add(new_db_token)
    await db.commit()

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    token_in: TokenRefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Logout current user and revoke their refresh token hash in DB."""
    # We simply hash the request token and mark it revoked
    hashed_rt = hash_token(token_in.refresh_token)
    rt_res = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hashed_rt)
    )
    db_token = rt_res.scalar_one_or_none()

    if db_token:
        db_token.is_revoked = True
        await log_security_event(db, db_token.user_id, "logout", request)
        await log_event(db, request, "logout", user_id=db_token.user_id)
        await db.commit()

    return {"message": "Logged out successfully"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Generate and mock mail password recovery links (protects against user enumeration)."""
    user_res = await db.execute(select(User).where(User.email == body.email))
    user = user_res.scalar_one_or_none()

    # Generic response returned always to hide whether the user exists or not
    success_msg = {
        "message": "If the email is registered, a password recovery link has been sent."
    }

    if user and user.is_active and not user.is_deleted:
        reset_token = create_password_reset_token(user.email, user.password_hash)
        mail_service = get_mail_service()
        await mail_service.send_password_reset_email(user.email, reset_token)
        await log_security_event(db, user.id, "password_reset_requested", request)
        await db.commit()

    return success_msg


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Verify reset token validity and reset user's password."""
    invalid_token_exc = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired reset token",
    )
    try:
        payload = decode_token(body.token)
        email = payload.get("sub")
        token_type = payload.get("type")
        token_checksum = payload.get("checksum")

        if email is None or token_type != "password_reset" or token_checksum is None:
            raise invalid_token_exc
    except JWTError:
        raise invalid_token_exc

    # Query the user
    user_res = await db.execute(select(User).where(User.email == email))
    user = user_res.scalar_one_or_none()
    if user is None or not user.is_active or user.is_deleted:
        raise invalid_token_exc

    # Validate that the token has not been used (compare current checksum vs token checksum)
    current_checksum = hashlib.md5(user.password_hash.encode("utf-8")).hexdigest()
    if current_checksum != token_checksum:
        raise invalid_token_exc

    # Update password and clear failed attempts
    user.password_hash = get_password_hash(body.new_password)
    user.failed_login_attempts = 0
    user.locked_until = None

    await log_security_event(db, user.id, "password_reset_success", request)
    await db.commit()

    return {"message": "Password has been reset successfully"}


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Modify user's password after validating their current password."""
    if not verify_password(body.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    current_user.password_hash = get_password_hash(body.new_password)
    await log_security_event(db, current_user.id, "password_change", request)
    await db.commit()

    return {"message": "Password changed successfully"}
