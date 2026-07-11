from typing import Any

class CustomerJourneySimulatorService:
    """Simulates customer checkout journey pathways and predicts conversion optimization lifts."""

    def simulate_journey(self, segment: str) -> dict[str, Any]:
        """
        Compare current (baseline) journey maps with optimized AI journey flows.
        """
        seg_lower = segment.lower()
        
        # Default baseline
        current_steps = ["Homepage", "Product Catalog", "Shopping Cart", "Exit (Abandonment)"]
        current_conv = 2.4  # percentage
        
        # Default AI recommendation
        optimized_steps = ["Homepage", "AI Personalized Recommendations", "Coupon Discount Dialog", "Checkout", "Purchase Confirmation"]
        optimized_conv = 14.8
        
        dropoffs = [
            {"step": "AI Personalized Recommendations", "drop_pct": 20},
            {"step": "Coupon Discount Dialog", "drop_pct": 10},
            {"step": "Checkout", "drop_pct": 15}
        ]
        
        improvements = [
            "Inject personalized recommendations above the fold to keep shoppers engaged.",
            "Display an exit-intent discount pop-up to capture cart abandons.",
            "Simplify fields in checkout to reduce form fatigue."
        ]

        if "vip" in seg_lower:
            current_conv = 8.5
            optimized_conv = 24.2
            improvements.insert(0, "Provide VIP express checkout options with single-click buy.")
        elif "at-risk" in seg_lower:
            current_conv = 1.1
            optimized_conv = 11.5
            improvements.insert(0, "Email a high-value discount coupon automatically before exit.")

        lift = optimized_conv - current_conv
        
        return {
            "segment": segment,
            "current_journey": {
                "steps": current_steps,
                "conversion_probability": round(current_conv, 1)
            },
            "optimized_journey": {
                "steps": optimized_steps,
                "conversion_probability": round(optimized_conv, 1)
            },
            "conversion_lift_pct": round(lift, 1),
            "drop_off_points": dropoffs,
            "suggested_improvements": improvements
        }

journey_simulator = CustomerJourneySimulatorService()
