from typing import Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_action import AgentAction
from app.models.agent_learning import AgentLearning


class AgentMemory:
    """Manages the long-term context, logs, and historical statistics of Agent actions directly from database."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_memory_metrics(self) -> dict[str, Any]:
        """
        Calculates memory insights over the last 500 actions.
        """
        # Fetch last 500 actions
        stmt = select(AgentAction).order_by(AgentAction.created_at.desc()).limit(500)
        res = await self.db.execute(stmt)
        actions = res.scalars().all()

        total = len(actions)
        completed = len([a for a in actions if a.status == "COMPLETED"])
        failed = len([a for a in actions if a.status == "FAILED"])
        pending = len([a for a in actions if a.status == "PENDING"])
        rejected = len([a for a in actions if a.status == "REJECTED"])

        # Success / Failure counts from learning history
        stmt_learn = select(AgentLearning).limit(500)
        res_learn = await self.db.execute(stmt_learn)
        learnings = res_learn.scalars().all()
        
        successful_learnings = len([l for l in learnings if l.success])
        failed_learnings = len(learnings) - successful_learnings

        # Average revenue lift
        lifts = [l.revenue_after - l.revenue_before for l in learnings if l.revenue_after > l.revenue_before]
        avg_revenue_lift = sum(lifts) / len(lifts) if lifts else 0.0

        # Average execution time
        exec_times = [a.execution_time_ms for a in actions if a.execution_time_ms is not None]
        avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0.0

        # Most common issue categories
        issue_counts = {}
        for a in actions:
            clean_issue = a.source_issue.split("-")[0] if "-" in a.source_issue else a.source_issue
            issue_counts[clean_issue] = issue_counts.get(clean_issue, 0) + 1
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        common_issues = [{"issue": k, "count": v} for k, v in sorted_issues[:3]]

        # Average confidence
        confidences = [a.confidence for a in actions]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.90

        return {
            "total_decisions": total,
            "completed_actions": completed,
            "failed_actions": failed,
            "pending_actions": pending,
            "rejected_actions": rejected,
            "learning_success_count": successful_learnings,
            "learning_failure_count": failed_learnings,
            "average_revenue_lift": round(avg_revenue_lift, 2),
            "average_execution_time_ms": round(avg_exec_time, 1),
            "average_confidence": round(avg_confidence * 100, 1),
            "common_issues": common_issues
        }

    async def get_history_logs(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Retrieves the timeline execution log of actions.
        """
        stmt = select(AgentAction).where(AgentAction.status.in_(["COMPLETED", "FAILED", "REJECTED"])).order_by(AgentAction.created_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        actions = res.scalars().all()

        logs = []
        for a in actions:
            logs.append({
                "id": a.id,
                "action": a.title,
                "status": a.status,
                "impact": a.execution_result or "No outcome registered.",
                "timestamp": a.executed_at.strftime("%Y-%m-%d %H:%M") if a.executed_at else a.created_at.strftime("%Y-%m-%d %H:%M")
            })
        return logs
