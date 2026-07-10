from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard envelope response format for storefront APIs."""

    success: bool = True
    message: str | None = None
    data: T | None = None
