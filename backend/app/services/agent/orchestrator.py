from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_action import AgentAction
from app.services.agent.observer import ObserverModule
from app.services.agent.analyzer import AnalyzerModule
from app.services.agent.planner import PlannerModule
from app.services.agent.approval import ApprovalModule
from app.services.agent.learner import LearnerModule
from app.services.agent.memory import AgentMemory


class AgentOrchestrator:
    """Coordinates agent loop stages: Observe -> Analyze -> Plan -> Approval -> Execute -> Learn."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.observer = ObserverModule(db)
        self.analyzer = AnalyzerModule()
        self.planner = PlannerModule(db)
        self.learner = LearnerModule(db)
        self.memory = AgentMemory(db)

    async def run_orchestrator_loop(self) -> list[dict[str, Any]]:
        """
        Runs the first part of the loop (Observe -> Analyze -> Plan) autonomously.
        Proposes multiple plans for the detected issues and saves them to the DB.
        """
        # 1. Observe
        obs = await self.observer.observe_environment()

        # 2. Analyze
        issues = self.analyzer.analyze_observations(obs)

        # 3. Plan
        actions = await self.planner.construct_plans(issues)
        
        return [
            {
                "id": a.id,
                "action_type": a.action_type,
                "title": a.title,
                "description": a.description,
                "priority": a.priority,
                "status": a.status,
                "source_issue": a.source_issue,
                "confidence": a.confidence,
                "reasoning": a.reasoning
            }
            for a in actions
        ]

    async def get_orchestrator_status(self) -> dict[str, Any]:
        """
        Gathers real e-commerce metrics, current active plans, pending approvals, and historical stats.
        """
        # 1. Observe
        obs = await self.observer.observe_environment()

        # 2. Analyze
        issues = self.analyzer.analyze_observations(obs)

        # 3. Fetch active pending actions from database
        stmt_pending = select(AgentAction).where(AgentAction.status == "PENDING").order_by(AgentAction.created_at.desc())
        res_pending = await self.db.execute(stmt_pending)
        pending_list = res_pending.scalars().all()

        # 4. Fetch history and statistics from memory module
        history = await self.memory.get_history_logs()
        memory_stats = await self.memory.get_memory_metrics()

        # 5. Fetch learning statistics
        learnings = await self.learner.get_summary_statistics()

        # Determine agent active state
        state = "idle"
        if pending_list:
            state = "awaiting_approval"
        elif issues:
            state = "reasoning"

        return {
            "status": "active",
            "state": state,  # "idle" | "perceiving" | "reasoning" | "awaiting_approval"
            "observations": obs,
            "findings": issues,
            "pending_approvals": [
                {
                    "id": p.id,
                    "action_type": p.action_type,
                    "title": p.title,
                    "description": p.description,
                    "priority": p.priority,
                    "status": p.status,
                    "source_issue": p.source_issue,
                    "confidence": p.confidence,
                    "reasoning": p.reasoning
                }
                for p in pending_list
            ],
            "execution_history": history,
            "learning_statistics": learnings,
            "memory_statistics": memory_stats
        }
