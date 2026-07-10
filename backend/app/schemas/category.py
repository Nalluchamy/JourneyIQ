from pydantic import BaseModel, ConfigDict


class CategoryRead(BaseModel):
    """Category response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None = None
