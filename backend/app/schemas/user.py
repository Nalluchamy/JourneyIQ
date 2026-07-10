import datetime

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    """User response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    phone: str | None = None
    role: str
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime


class UserUpdate(BaseModel):
    """User profile update schema."""

    full_name: str | None = None
    phone: str | None = None
