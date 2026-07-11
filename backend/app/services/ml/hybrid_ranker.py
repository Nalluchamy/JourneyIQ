from typing import Any
from app.models.product import Product


class HybridRanker:
    """Weighted ranking compiler combining collaborative, content, and popularity models."""

    def __init__(
        self,
        weight_collab: float = 0.5,
        weight_content: float = 0.3,
        weight_pop: float = 0.2,
    ):
        self.w_collab = weight_collab
        self.w_content = weight_content
        self.w_pop = weight_pop

    def rank_for_user(
        self,
        user_id: int,
        products: list[Product],
        user_interactions: dict[tuple[int, int], float],
        user_similarities: dict[tuple[int, int], float],
        content_similarities: dict[int, list[tuple[int, float]]],  # product_id -> [(similar_prod_id, score)]
        popularity_metrics: dict[str, list[tuple[int, float]]],
        purchased_product_names: dict[int, str],  # product_id -> product_name
        user_purchases: set[int],  # set of product_ids bought by user
    ) -> list[dict[str, Any]]:
        """
        Calculates hybrid score for each product for the target user.
        Excludes products already purchased.
        """
        ranked_list: list[dict[str, Any]] = []

        # Convert user similarities to list of (similar_user_id, similarity)
        similar_users = [
            (u2, sim) for (u1, u2), sim in user_similarities.items()
            if u1 == user_id and sim > 0
        ]
        similar_users.sort(key=lambda x: x[1], reverse=True)

        # Popularity metrics pre-processing
        best_sellers = {p_id: score for p_id, score in popularity_metrics.get("best_selling", [])}
        highest_rated = {p_id: score for p_id, score in popularity_metrics.get("highest_rated", [])}
        trending = {p_id: score for p_id, score in popularity_metrics.get("trending", [])}

        for prod in products:
            # Exclude already purchased items to ensure freshness
            if prod.id in user_purchases:
                continue

            # 1. Collaborative score: Average weight of interactions from similar users
            collab_score = 0.0
            collab_count = 0
            for sim_user, sim_weight in similar_users:
                sim_interaction = user_interactions.get((sim_user, prod.id), 0.0)
                if sim_interaction > 0:
                    collab_score += sim_interaction * sim_weight
                    collab_count += 1
            if collab_count > 0:
                collab_score /= collab_count

            # 2. Content score: Based on user's past interaction history with similar products
            content_score = 0.0
            content_count = 0
            user_interacted_prods = [p_id for (u, p_id), w in user_interactions.items() if u == user_id and w > 0]
            
            for interacted_pid in user_interacted_prods:
                sim_list = content_similarities.get(interacted_pid, [])
                match = next((sim for pid, sim in sim_list if pid == prod.id), 0.0)
                if match > 0:
                    content_score += match
                    content_count += 1
            if content_count > 0:
                content_score /= content_count

            # 3. Popularity score: Combine standard listing scores
            pop_score = 0.0
            pop_reasons = []
            if prod.id in best_sellers:
                pop_score += 1.0
                pop_reasons.append("best-selling")
            if prod.id in highest_rated:
                pop_score += 1.0
                pop_reasons.append("highly rated")
            if prod.id in trending:
                pop_score += 1.0
                pop_reasons.append("trending")

            # Weighted Hybrid Total
            hybrid_score = (
                (self.w_collab * collab_score) +
                (self.w_content * content_score) +
                (self.w_pop * pop_score)
            )

            # Determine explainability explanation
            explanation = "Popular among customers similar to you."
            if user_purchases:
                # Find if this product is similar to a purchased product
                found_match = False
                for purchased_id in user_purchases:
                    sim_list = content_similarities.get(purchased_id, [])
                    match = next((sim for pid, sim in sim_list if pid == prod.id), 0.0)
                    if match > 0.6:
                        purchased_name = purchased_product_names.get(purchased_id, "items you bought")
                        explanation = f"Recommended because you bought {purchased_name}."
                        found_match = True
                        break
                if not found_match and content_score > 0.4:
                    explanation = "Similar to products you have viewed."
            
            if explanation == "Popular among customers similar to you." and prod.id in trending:
                explanation = "Trending this week."
            elif explanation == "Popular among customers similar to you." and prod.id in highest_rated:
                explanation = "Highly rated by customers like you."

            ranked_list.append({
                "product_id": prod.id,
                "score": round(hybrid_score, 4),
                "explanation": explanation
            })

        # Sort ranked list descending by hybrid score
        ranked_list.sort(key=lambda x: x["score"], reverse=True)
        return ranked_list
