from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.deep_learning.predict import NCFPredictor

logger = structlog.get_logger()


class NCFInferenceService:
    """NCF Deep Learning Inference client interface wrapper."""

    def __init__(self):
        self.predictor = NCFPredictor()

    async def recommend_for_user(
        self, user_id: int, db: AsyncSession, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Retrieve top product recommendations for user_id."""
        return await self.predictor.recommend_for_user(user_id, db, limit=limit)

    async def similar_products(
        self, product_id: int, db: AsyncSession, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Retrieve top products similar to product_id."""
        return await self.predictor.similar_products(product_id, db, limit=limit)

    async def predict_score(self, user_id: int, product_id: int) -> float:
        """Calculate recommendation likelihood score (0.0 to 1.0)."""
        return await self.predictor.predict_score(user_id, product_id)
