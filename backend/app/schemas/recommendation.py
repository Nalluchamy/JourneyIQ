import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.product import ProductRead


class RecommendationRead(BaseModel):
    """Personalized recommendation response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_id: int
    score: float
    explanation: str | None = None
    created_at: datetime.datetime | None = None  # Mapping generated_at
    product: ProductRead


from typing import Any


class DeepRecommendationRead(BaseModel):
    """Deep learning recommendation response schema."""

    model_config = ConfigDict(from_attributes=True)

    product: ProductRead
    score: float
    explanation: str | None = None


class ModelComparisonRead(BaseModel):
    """Model comparison schema for hybrid vs deep learning models."""

    hybrid: list[DeepRecommendationRead]
    deep: list[DeepRecommendationRead]
    metadata: dict[str, Any]
    metrics: dict[str, Any]

