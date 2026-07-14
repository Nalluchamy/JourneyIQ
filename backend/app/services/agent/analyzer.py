from typing import Any


class AnalyzerModule:
    """Evaluates telemetry values to classify storefront anomalies and rate priority levels."""

    def analyze_observations(self, obs: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Analyze observed data and output list of issues.
        """
        issues = []

        # 1. Critical priority check: Revenue Drop
        rev = obs.get("revenue", {})
        drop_pct = rev.get("drop_pct", 0.0)
        if drop_pct >= 20.0:
            issues.append({
                "issue_type": "REVENUE_DROP",
                "priority": "CRITICAL",
                "confidence": 0.95,
                "reason": f"Revenue dropped by {drop_pct}% today (₹{rev.get('today'):,.2f}) compared to yesterday (₹{rev.get('yesterday'):,.2f}).",
                "affected_objects": ["Storefront Revenue Engine"]
            })

        # 2. Critical priority check: Out of Stock
        inv = obs.get("inventory", {})
        out_of_stock_count = inv.get("out_of_stock_count", 0)
        if out_of_stock_count > 0:
            issues.append({
                "issue_type": "OUT_OF_STOCK",
                "priority": "CRITICAL",
                "confidence": 0.98,
                "reason": f"{out_of_stock_count} active product(s) are completely out of stock.",
                "affected_objects": inv.get("out_of_stock_products", [])
            })

        # 3. Critical priority check: Payment Failures
        pay = obs.get("payments", {})
        fail_rate = pay.get("payment_failure_rate", 0.0)
        if fail_rate > 10.0:
            issues.append({
                "issue_type": "PAYMENT_FAILURE",
                "priority": "CRITICAL",
                "confidence": 0.92,
                "reason": f"Failed payment transactions are high ({fail_rate}% of total today). Check payment gateways.",
                "affected_objects": ["Payment Provider API Gateway"]
            })

        # 4. High priority check: Low Stock
        low_stock_count = inv.get("low_stock_count", 0)
        if low_stock_count > 0:
            issues.append({
                "issue_type": "LOW_STOCK",
                "priority": "HIGH",
                "confidence": 0.90,
                "reason": f"{low_stock_count} products have stock below threshold (stock < 5).",
                "affected_objects": inv.get("low_stock_products", [])
            })

        # 5. High priority check: Declining Sentiment
        rev_stats = obs.get("reviews", {})
        pos_pct = rev_stats.get("positive_pct", 100.0)
        if pos_pct < 70.0 and rev_stats.get("total_reviews", 0) > 0:
            issues.append({
                "issue_type": "DECLINING_SENTIMENT",
                "priority": "HIGH",
                "confidence": 0.88,
                "reason": f"Positive reviews dropped to {pos_pct}%. Customer complaints are rising.",
                "affected_objects": ["Product Reviews Summary"]
            })

        # 6. Medium priority check: Cart Abandonment
        cart = obs.get("cart", {})
        abandoned_count = cart.get("abandoned_carts_count", 0)
        if abandoned_count >= 5:
            issues.append({
                "issue_type": "CART_ABANDONMENT",
                "priority": "MEDIUM",
                "confidence": 0.85,
                "reason": f"{abandoned_count} shopping carts have been inactive for over 2 hours without order checkout completion.",
                "affected_objects": ["Shopping Cart Pipeline"]
            })

        # 7. Low priority check: Slow Products
        sales_perf = obs.get("sales_performance", {})
        slow_selling = sales_perf.get("slow_selling", [])
        if slow_selling:
            issues.append({
                "issue_type": "SLOW_PRODUCT",
                "priority": "LOW",
                "confidence": 0.80,
                "reason": f"{len(slow_selling)} product(s) have zero orders registered in the last 7 days.",
                "affected_objects": [item["name"] for item in slow_selling[:3]]
            })

        # 8. Low priority check: Recommendation Model Degradation
        rec_metrics = obs.get("recommendation_metrics", {})
        precision = rec_metrics.get("precision_at_10", 0.0)
        if precision > 0.0 and precision < 0.05:
            issues.append({
                "issue_type": "MODEL_DEGRADATION",
                "priority": "LOW",
                "confidence": 0.85,
                "reason": f"PyTorch NCF recommendation model precision@10 dropped to {precision:.4f} (threshold: 0.05).",
                "affected_objects": ["PyTorch Neural Collaborative Filtering Model"]
            })

        return issues
