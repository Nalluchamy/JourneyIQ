from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent.perception import PerceptionModule
from app.services.agent.reasoning import ReasoningModule
from app.services.agent.planning import PlanningModule
from app.services.agent.safety import agent_safety
from app.services.agent.memory import agent_memory
from app.services.agent.learning import agent_learning


class AgentOrchestrator:
    """Coordinates agent loop stages: Perceive -> Memory -> Reason -> Plan -> Exec -> Learn."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.perception = PerceptionModule(db)
        self.reasoning = ReasoningModule()
        self.planning = PlanningModule()

    async def get_orchestrator_status(self) -> dict[str, Any]:
        """
        Runs the full pipeline to evaluate current alerts, anomalies, plans, and learning statistics.
        """
        # 1. Perceive
        obs = await self.perception.observe_environment()
        
        # 2. Reason
        findings = self.reasoning.evaluate_observations(obs)
        
        # 3. Plan
        plans = self.planning.construct_plans(findings)
        
        # Add generated plans to safety approval queue if they require approval
        for plan in plans:
            if plan["requires_approval"]:
                agent_safety.add_to_queue(plan)

        # 4. Get active pending queue
        pending = agent_safety.get_pending()

        # 5. Retrieve history from memory
        history = agent_memory.get_history()

        # 6. Retrieve learnings
        learnings = agent_learning.compile_learning_statistics()

        # Determine agent active state
        state = "idle"
        if pending:
            state = "awaiting_approval"
        elif findings:
            state = "reasoning"

        return {
            "status": "active",
            "state": state,  # "idle" | "perceiving" | "reasoning" | "awaiting_approval"
            "observations": obs,
            "findings": findings,
            "proposed_plans": plans,
            "pending_approvals": pending,
            "execution_history": history,
            "learning_statistics": learnings
        }
