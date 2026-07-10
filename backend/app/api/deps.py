from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

# Standard OAuth2 scheme pointing to our login endpoint for Swagger Bearer Auth integration
reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(reusable_oauth2)],
) -> User:
    """Dependency to retrieve and validate the currently authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id_str: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")

        if user_id_str is None or token_type != "access":
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    # Query the user in the database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Inactive or soft-deleted users are blocked
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    if user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User account is deleted"
        )

    return user


def require_role(allowed_roles: list[str]) -> Any:
    """Helper factory generating role checker dependencies."""

    def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Access restricted. Requires one of roles: {allowed_roles}",
            )
        return current_user

    return role_checker


# Reusable guard dependencies
require_customer = Depends(require_role(["customer"]))
require_staff = Depends(require_role(["staff"]))
require_owner = Depends(require_role(["owner"]))
require_admin = Depends(require_role(["admin"]))
