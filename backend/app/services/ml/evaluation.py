
import structlog

logger = structlog.get_logger()


class RecommenderEvaluator:
    """Computes precision, recall, coverage, diversity, and hit-rate quality metrics."""

    @staticmethod
    def evaluate(
        recommendations: dict[int, list[int]],  # user_id -> recommended product_ids
        ground_truth: dict[int, list[int]],     # user_id -> actual purchased/interacted product_ids
        all_product_ids: list[int],
        k: int = 5,
    ) -> dict[str, float]:
        """
        Calculates recommendation metrics.
        - Precision@K: Proportion of recommended items that are relevant.
        - Recall@K: Proportion of relevant items that are recommended.
        - Hit Rate: Proportion of users for whom at least one recommended item is relevant.
        - Coverage: Proportion of unique products recommended across all users.
        - Diversity: Uniqueness index based on unique product IDs recommended.
        """
        precision_sum = 0.0
        recall_sum = 0.0
        hits = 0
        total_users = len(ground_truth)

        all_recommended_items: set[int] = set()

        for u_id, actuals in ground_truth.items():
            preds = recommendations.get(u_id, [])[:k]
            if not preds or not actuals:
                continue

            all_recommended_items.update(preds)

            # Overlaps
            hits_set = set(preds) & set(actuals)

            # Precision@K
            precision_sum += len(hits_set) / len(preds)

            # Recall@K
            recall_sum += len(hits_set) / len(actuals)

            if len(hits_set) > 0:
                hits += 1

        # Averages
        avg_precision = precision_sum / total_users if total_users > 0 else 0.0
        avg_recall = recall_sum / total_users if total_users > 0 else 0.0
        hit_rate = hits / total_users if total_users > 0 else 0.0

        # Coverage
        coverage = len(all_recommended_items) / len(all_product_ids) if all_product_ids else 0.0

        # Diversity (simplified as the ratio of unique recommendations over total recommendation slots)
        total_slots = total_users * k
        diversity = len(all_recommended_items) / total_slots if total_slots > 0 else 0.0

        metrics = {
            f"precision_at_{k}": round(avg_precision, 4),
            f"recall_at_{k}": round(avg_recall, 4),
            "hit_rate": round(hit_rate, 4),
            "coverage": round(coverage, 4),
            "diversity": round(diversity, 4),
        }

        # Log metrics to structlog
        logger.info(
            "Recommendation Engine Evaluation completed",
            metrics=metrics,
            k=k,
            total_users_evaluated=total_users
        )

        return metrics
