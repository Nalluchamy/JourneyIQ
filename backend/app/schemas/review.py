from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserRead


class ReviewRead(BaseModel):
    """Review read schema including details of the user who posted it."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_id: int
    rating: int = Field(..., ge=1, le=5)
    review: str | None = None
    user: UserRead


class ReviewCreate(BaseModel):
    """Review creation schema with 1-5 rating constraint."""

    rating: int = Field(..., ge=1, le=5, description="Rating must be between 1 and 5")
    review: str | None = Field(None, max_length=2000, description="Review text comment")


class ReviewUpdate(BaseModel):
    """Review update schema allowing partial edits."""

    rating: int | None = Field(None, ge=1, le=5, description="Rating must be between 1 and 5")
    review: str | None = Field(None, max_length=2000, description="Review text comment")
