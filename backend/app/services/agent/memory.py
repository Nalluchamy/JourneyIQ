from typing import Any

class AgentMemory:
    """Manages the history of actions, decisions, and learning indices for the Agentic AI orchestrator."""

    def __init__(self) -> None:
        self.decision_history: list[dict[str, Any]] = [
            {
                "id": "1",
                "action": "A/B test launch for new layouts",
                "status": "completed",
                "impact": "Conversion improved by 2.4%",
                "timestamp": "2026-07-10 14:32"
            },
            {
                "id": "2",
                "action": "Restock notification to supply managers",
                "status": "completed",
                "impact": "Restocked 12 critical units",
                "timestamp": "2026-07-11 09:15"
            }
        ]
        self.rejected_plans: list[dict[str, Any]] = []

    def get_history(self) -> list[dict[str, Any]]:
        return self.decision_history

    def log_decision(self, action_desc: str, status: str, impact: str = "Pending evaluation") -> None:
        import datetime
        self.decision_history.insert(0, {
            "id": str(len(self.decision_history) + 1),
            "action": action_desc,
            "status": status,
            "impact": impact,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        })

    def log_rejection(self, plan_desc: str) -> None:
        self.rejected_plans.append({
            "plan": plan_desc,
            "timestamp": "Now"
        })


agent_memory = AgentMemory()
