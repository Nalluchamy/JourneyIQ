from typing import Any

class ReasoningModule:
    """Evaluates metrics anomalies (dropoffs, stock limits, sentiment drops) and documents justifications."""

    def evaluate_observations(self, observations: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Processes observations and yields structured findings.
        """
        findings = []

        # 1. Churn / Abandonment check
        abandon_rate = observations.get("cart_abandonment_rate", 0.0)
        if abandon_rate > 35.0:
            findings.append({
                "anomaly": "High Cart Abandonment",
                "severity": "HIGH",
                "evidence": f"Cart abandonment rate is at {abandon_rate}%.",
                "reasoning": "Customers are leaving items in their cart without checking out. This is usually caused by price surprises, lack of trust, or complex checkout forms."
            })

        # 2. Stockout check
        low_stock = observations.get("low_stock_count", 0)
        if low_stock > 0:
            findings.append({
                "anomaly": "Product Stockout Risk",
                "severity": "MEDIUM",
                "evidence": f"{low_stock} products have stock <= 5.",
                "reasoning": f"Products like {', '.join(observations.get('low_stock_products', []))} are running low, threatening potential purchase opportunities."
            })

        # 3. Sentiment check
        sentiment = observations.get("overall_sentiment_pct", 100.0)
        if sentiment < 75.0:
            findings.append({
                "anomaly": "Declining Customer Sentiment",
                "severity": "HIGH",
                "evidence": f"Positive reviews are down to {sentiment}%.",
                "reasoning": f"Review descriptions indicate complaints about '{observations.get('top_complaint', 'quality')}'."
            })

        return findings
