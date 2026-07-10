from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated envelope for list endpoints."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int
