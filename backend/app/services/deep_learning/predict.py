import os
from typing import Any

import numpy as np
import structlog
import torch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.event import Event
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.recommendation import Recommendation
from app.services.deep_learning.model import NCFModel
from app.services.deep_learning.utils import get_device

logger = structlog.get_logger()
MODEL_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "models")
)
LATEST_PATH = os.path.join(MODEL_DIR, "latest.pt")


class NCFPredictor:
    """Handles loading the trained NCF model and generating predictions & similar items."""

    def __init__(self):
        self.device = get_device()
        self.model = None
        self.user_to_idx = {}
        self.product_to_idx = {}
        self.idx_to_user = {}
        self.idx_to_product = {}
        self.is_loaded = False
        self._load_model()

    def _load_model(self) -> None:
        """Loads NCF checkpoint from models/latest.pt."""
        if not os.path.exists(LATEST_PATH):
            logger.warning(
                "NCF model latest.pt checkpoint not found. Caching cold start state."
            )
            return

        try:
            checkpoint = torch.load(LATEST_PATH, map_location=self.device)
            self.user_to_idx = checkpoint["user_to_idx"]
            self.product_to_idx = checkpoint["product_to_idx"]
            self.idx_to_user = checkpoint["idx_to_user"]
            self.idx_to_product = checkpoint["idx_to_product"]

            # Map index mappings keys back to integer if they got serialized as strings
            self.user_to_idx = {int(k): int(v) for k, v in self.user_to_idx.items()}
            self.product_to_idx = {
                int(k): int(v) for k, v in self.product_to_idx.items()
            }
            self.idx_to_user = {int(k): int(v) for k, v in self.idx_to_user.items()}
            self.idx_to_product = {
                int(k): int(v) for k, v in self.idx_to_product.items()
            }

            self.model = NCFModel(
                num_users=checkpoint["num_users"],
                num_products=checkpoint["num_products"],
                embedding_dim=checkpoint["embedding_dim"],
                layers=checkpoint["layers"],
            ).to(self.device)

            self.model.load_dict = checkpoint["state_dict"]
            self.model.load_state_dict(checkpoint["state_dict"])
            self.model.eval()
            self.is_loaded = True
            logger.info(
                "Successfully loaded NCF model checkpoint",
                version=checkpoint.get("version_id"),
            )
        except Exception as e:
            logger.error("Failed to load NCF model checkpoint", error=str(e))

    async def predict_score(self, user_id: int, product_id: int) -> float:
        """Returns the recommendation score (0-1) for a user and product."""
        if not self.is_loaded or self.model is None:
            return 0.0

        user_idx = self.user_to_idx.get(user_id)
        product_idx = self.product_to_idx.get(product_id)

        if user_idx is None or product_idx is None:
            return 0.0

        u_tensor = torch.tensor([user_idx], dtype=torch.long).to(self.device)
        p_tensor = torch.tensor([product_idx], dtype=torch.long).to(self.device)

        with torch.no_grad():
            score = self.model(u_tensor, p_tensor).item()
        return float(score)

    async def similar_products(
        self, product_id: int, db: AsyncSession, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Computes product similarity by calculating cosine similarity of product embeddings.
        Falls back to category matching if model is not loaded.
        """
        # Ensure active product exists
        target_prod = (
            await db.execute(
                select(Product).where(
                    Product.id == product_id,
                    Product.is_deleted == False,
                    Product.is_active == True,
                )
            )
        ).scalar_one_or_none()
        if not target_prod:
            return []

        if (
            not self.is_loaded
            or self.model is None
            or product_id not in self.product_to_idx
        ):
            # Fallback: same category products
            fallback_stmt = (
                select(Product)
                .where(
                    Product.category_id == target_prod.category_id,
                    Product.id != product_id,
                    Product.is_deleted == False,
                    Product.is_active == True,
                )
                .limit(limit)
            )
            fallback_prods = (await db.execute(fallback_stmt)).scalars().all()
            return [
                {
                    "product": p,
                    "score": 0.5,
                    "explanation": "High similarity in category and brand.",
                }
                for p in fallback_prods
            ]

        # NCF Embedding Similarity
        try:
            prod_idx = self.product_to_idx[product_id]
            prod_embeddings = self.model.product_embedding.weight.data.cpu().numpy()
            target_vector = prod_embeddings[prod_idx]

            # Cosine similarity
            norms = np.linalg.norm(prod_embeddings, axis=1)
            target_norm = np.linalg.norm(target_vector)

            # Avoid divide by zero
            norms[norms == 0] = 1e-8
            if target_norm == 0:
                target_norm = 1e-8

            similarities = np.dot(prod_embeddings, target_vector) / (
                norms * target_norm
            )

            # Sort products index
            sorted_indices = np.argsort(similarities)[::-1]

            similar_items = []
            for idx in sorted_indices:
                p_id = self.idx_to_product.get(idx)
                if p_id is None or p_id == product_id:
                    continue

                # Fetch product
                prod = (
                    await db.execute(
                        select(Product).where(
                            Product.id == p_id,
                            Product.is_deleted == False,
                            Product.is_active == True,
                        )
                    )
                ).scalar_one_or_none()
                if prod:
                    similar_items.append(
                        {
                            "product": prod,
                            "score": float(similarities[idx]),
                            "explanation": "High similarity in category and brand.",
                        }
                    )
                    if len(similar_items) >= limit:
                        break
            return similar_items
        except Exception as e:
            logger.error("Error computing embedding similarities", error=str(e))
            return []

    async def recommend_for_user(
        self, user_id: int, db: AsyncSession, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Generates personalized product recommendations using NCF scores.
        Handles cold-starts automatically by falling back to Hybrid Recommender or Trending.
        """
        # Cold start fallback if NCF not loaded or user not in embeddings
        user_idx = self.user_to_idx.get(user_id)
        if not self.is_loaded or self.model is None or user_idx is None:
            logger.info(
                "Cold-start user or uninitialized NCF. Falling back to Hybrid recommendations.",
                user_id=user_id,
            )
            # Query existing hybrid recommendations
            hybrid_stmt = (
                select(Recommendation)
                .where(Recommendation.user_id == user_id)
                .options(selectinload(Recommendation.product))
                .order_by(Recommendation.score.desc())
                .limit(limit)
            )
            recs = (await db.execute(hybrid_stmt)).scalars().all()
            if recs:
                return [
                    {
                        "product": r.product,
                        "score": float(r.score),
                        "explanation": r.explanation,
                    }
                    for r in recs
                    if r.product
                ]

            # Absolute fallback: trending views
            trend_stmt = (
                select(Product)
                .join(Event, Event.product_id == Product.id)
                .where(
                    Event.event_type == "view_item",
                    Product.is_deleted == False,
                    Product.is_active == True,
                )
                .group_by(Product.id)
                .limit(limit)
            )
            trend_prods = (await db.execute(trend_stmt)).scalars().all()
            return [
                {"product": p, "score": 1.0, "explanation": "Trending this week."}
                for p in trend_prods
            ]

        try:
            # Query all active product database IDs
            prods_stmt = select(Product).where(
                Product.is_deleted == False, Product.is_active == True
            )
            products = (await db.execute(prods_stmt)).scalars().all()

            # Fetch user past purchases
            order_stmt = (
                select(OrderItem.product_id).join(Order).where(Order.user_id == user_id)
            )
            purchased_pids = set((await db.execute(order_stmt)).scalars().all())

            # Fetch user view events
            view_stmt = select(Event.product_id).where(
                Event.user_id == user_id,
                Event.event_type == "view_item",
                Event.product_id.isnot(None),
            )
            viewed_pids = set((await db.execute(view_stmt)).scalars().all())

            # Score all products
            scored_items = []

            # Prepare tensors for batch evaluation
            p_ids_to_evaluate = []
            p_indices_to_evaluate = []

            for prod in products:
                # Filter out already purchased items to ensure new recommendations
                if prod.id in purchased_pids:
                    continue
                p_idx = self.product_to_idx.get(prod.id)
                if p_idx is not None:
                    p_ids_to_evaluate.append(prod)
                    p_indices_to_evaluate.append(p_idx)

            if p_indices_to_evaluate:
                u_tensor = torch.tensor(
                    [user_idx] * len(p_indices_to_evaluate), dtype=torch.long
                ).to(self.device)
                p_tensor = torch.tensor(p_indices_to_evaluate, dtype=torch.long).to(
                    self.device
                )

                with torch.no_grad():
                    scores = self.model(u_tensor, p_tensor).cpu().numpy()

                for i, prod in enumerate(p_ids_to_evaluate):
                    score = float(scores[i])

                    # Generate explainable recommendation reason
                    if prod.id in viewed_pids:
                        explanation = "Based on products viewed."
                    elif any(p_idx in self.product_to_idx for p_idx in purchased_pids):
                        explanation = (
                            "Customers with similar purchase history bought this."
                        )
                    else:
                        explanation = "Frequently purchased together."

                    scored_items.append(
                        {"product": prod, "score": score, "explanation": explanation}
                    )

            # Sort and return top list
            scored_items.sort(key=lambda x: x["score"], reverse=True)
            return scored_items[:limit]
        except Exception as e:
            logger.error(
                "Error generating recommendations inside predictor", error=str(e)
            )
            return []
