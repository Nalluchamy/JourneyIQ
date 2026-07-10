from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.security import validate_password_strength


class UserRegister(BaseModel):
    """Registration input validation schema."""

    email: EmailStr
    password: str = Field(
        ..., min_length=8, description="Minimum 8 characters password"
    )
    full_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        """Validate password strength rules."""
        validate_password_strength(v)
        return v


class TokenResponse(BaseModel):
    """Authentication token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    email: str | None = None
    full_name: str | None = None


class TokenRefreshRequest(BaseModel):
    """Token refresh input validation schema."""

    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Forgot password request validation schema."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request validation schema."""

    token: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        validate_password_strength(v)
        return v


class ChangePasswordRequest(BaseModel):
    """Change password request validation schema."""

    old_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        validate_password_strength(v)
        return v
