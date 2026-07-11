from typing import Any

class SafetyModule:
    """Implements human-in-the-loop safety constraints, buffering sensitive campaign/pricing decisions."""

    def __init__(self) -> None:
        self.pending_actions: dict[str, dict[str, Any]] = {
            "action-1": {
                "id": "action-1",
                "title": "Trigger win-back coupon to Slipping customers",
                "description": "Send an automated 20% discount coupon to customers who haven't completed checkout in the last 48 hours.",
                "target_segment": "At-Risk Customers",
                "impact": "Expected to recover 12% of abandoned checkouts.",
                "requires_approval": True,
                "status": "pending"
            },
            "action-3": {
                "id": "action-3",
                "title": "Launch customer feedback follow-up campaign",
                "description": "Send feedback emails to buyers who rated products negatively to resolve customer issues.",
                "target_segment": "Dissatisfied Customers",
                "impact": "Improve storefront customer satisfaction ratings.",
                "requires_approval": True,
                "status": "pending"
            }
        }

    def get_pending(self) -> list[dict[str, Any]]:
        return list(self.pending_actions.values())

    def add_to_queue(self, action: dict[str, Any]) -> None:
        self.pending_actions[action["id"]] = {
            **action,
            "status": "pending"
        }

    def approve_action(self, action_id: str) -> dict[str, Any] | None:
        """Mark action as approved, removing it from queue or changing status."""
        if action_id in self.pending_actions:
            act = self.pending_actions.pop(action_id)
            act["status"] = "approved"
            return act
        return None

    def reject_action(self, action_id: str) -> dict[str, Any] | None:
        """Dismiss action, removing it from queue."""
        if action_id in self.pending_actions:
            act = self.pending_actions.pop(action_id)
            act["status"] = "rejected"
            return act
        return None


# Singleton safety queue
agent_safety = SafetyModule()
