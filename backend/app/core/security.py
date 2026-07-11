import datetime
import hashlib
import re
from typing import Any, cast

import bcrypt
from jose import jwt

from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify standard plain text password matches stored bcrypt hash using native bcrypt."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    """Generate bcrypt hash from plain text password using native bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def hash_token(token: str) -> str:
    """Hash refresh tokens using SHA-256 to prevent database log leakage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


import uuid


def create_access_token(
    subject: str | Any, expires_delta: datetime.timedelta | None = None
) -> str:
    """Generate short-lived access JWT with a unique jti claim."""
    if expires_delta:
        expire = datetime.datetime.now(datetime.UTC) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    return cast(
        str,
        jwt.encode(
            to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        ),
    )


def create_refresh_token(
    subject: str | Any, expires_delta: datetime.timedelta | None = None
) -> str:
    """Generate long-lived refresh JWT with a unique jti claim."""
    if expires_delta:
        expire = datetime.datetime.now(datetime.UTC) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    return cast(
        str,
        jwt.encode(
            to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        ),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode JWT token and return payload dictionary."""
    return cast(
        dict[str, Any],
        jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        ),
    )


def validate_password_strength(password: str) -> None:
    """Validate strength requirements: 8+ chars, uppercase, lowercase, digit, special char."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[@$!%*#?&^_\-+=|~`(){}[\]:;\"'<>,.?/]", password):
        raise ValueError("Password must contain at least one special character.")


def create_verification_token(email: str) -> str:
    """Create signed email verification token valid for 24 hours."""
    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24)
    to_encode = {"exp": expire, "sub": email, "type": "email_verification"}
    return cast(
        str,
        jwt.encode(
            to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        ),
    )


def create_password_reset_token(email: str, password_hash: str) -> str:
    """Create signed reset password token valid for 15 minutes.

    Stores a hash checksum of the user's password_hash to invalidate the link
    once the password is modified.
    """
    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        minutes=15
    )
    pw_hash_checksum = hashlib.md5(password_hash.encode("utf-8")).hexdigest()
    to_encode = {
        "exp": expire,
        "sub": email,
        "type": "password_reset",
        "checksum": pw_hash_checksum,
    }
    return cast(
        str,
        jwt.encode(
            to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        ),
    )
