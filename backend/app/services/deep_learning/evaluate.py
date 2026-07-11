import json
import math
import os

import structlog

logger = structlog.get_logger()
MODEL_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "models")
)


class DeepLearningEvaluator:
    """Computes Precision@K, Recall@K, F1 Score, Hit Rate, NDCG, and Coverage metrics for PyTorch model."""

    @staticmethod
    def calculate_ndcg(actuals: set[int], preds: list[int], k: int) -> float:
        """Computes Normalized Discounted Cumulative Gain (NDCG) at K."""
        dcg = 0.0
        for i, p in enumerate(preds[:k]):
            if p in actuals:
                dcg += 1.0 / math.log2(i + 2)

        # Ideal DCG: maximum possible hits placed at the top
        idcg = sum(1.0 / math.log2(idx + 2) for idx in range(min(len(actuals), k)))
        if idcg > 0:
            return dcg / idcg
        return 0.0

    @staticmethod
    def evaluate_and_save(
        recommendations: dict[int, list[int]],  # user_id -> recommended product_ids
        ground_truth: dict[int, list[int]],  # user_id -> actual interacted product_ids
        all_product_ids: list[int],
        k: int = 10,
    ) -> dict[str, float]:
        """
        Calculates recommendation benchmarks and dumps them into models/evaluation_metrics.json.
        """
        precision_sum = 0.0
        recall_sum = 0.0
        f1_sum = 0.0
        ndcg_sum = 0.0
        hits = 0
        total_users = len(ground_truth)

        all_recommended_items: set[int] = set()

        for u_id, actuals in ground_truth.items():
            actuals_set = set(actuals)
            preds = recommendations.get(u_id, [])[:k]
            if not preds or not actuals_set:
                continue

            all_recommended_items.update(preds)

            # Intersection
            hits_set = set(preds) & actuals_set
            num_hits = len(hits_set)

            # Precision@K
            p_k = num_hits / len(preds)
            precision_sum += p_k

            # Recall@K
            r_k = num_hits / len(actuals_set)
            recall_sum += r_k

            # F1 Score
            if p_k + r_k > 0:
                f1_sum += (2 * p_k * r_k) / (p_k + r_k)

            # NDCG@K
            ndcg_sum += DeepLearningEvaluator.calculate_ndcg(actuals_set, preds, k)

            if num_hits > 0:
                hits += 1

        # Calculate Averages
        avg_precision = precision_sum / total_users if total_users > 0 else 0.0
        avg_recall = recall_sum / total_users if total_users > 0 else 0.0
        avg_f1 = f1_sum / total_users if total_users > 0 else 0.0
        avg_ndcg = ndcg_sum / total_users if total_users > 0 else 0.0
        hit_rate = hits / total_users if total_users > 0 else 0.0

        # Coverage
        coverage = (
            len(all_recommended_items) / len(all_product_ids)
            if all_product_ids
            else 0.0
        )

        metrics = {
            f"precision_at_{k}": round(avg_precision, 4),
            f"recall_at_{k}": round(avg_recall, 4),
            f"f1_at_{k}": round(avg_f1, 4),
            "hit_rate": round(hit_rate, 4),
            "ndcg": round(avg_ndcg, 4),
            "coverage": round(coverage, 4),
        }

        os.makedirs(MODEL_DIR, exist_ok=True)
        metrics_json_path = os.path.join(MODEL_DIR, "evaluation_metrics.json")
        with open(metrics_json_path, "w") as f:
            json.dump(metrics, f, indent=2)

        logger.info("Deep learning evaluation computed and saved", metrics=metrics)
        return metrics
