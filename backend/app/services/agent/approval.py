import datetime
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models.agent_action import AgentAction
from app.models.audit_log import AuditLog
from app.services.agent.executor import ExecutorModule


class ApprovalModule:
    """Implements human-in-the-loop safety approvals for pending agent plans and audits decisions."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.executor = ExecutorModule(db)

    async def get_pending_actions(self) -> list[AgentAction]:
        """
        Retrieves all proposed plans currently awaiting owner review.
        """
        stmt = select(AgentAction).where(AgentAction.status == "PENDING").order_by(AgentAction.created_at.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def approve_action(self, action_id: int, user_id: int | None = None) -> AgentAction | None:
        """
        Marks an action as APPROVED, audits it, executes it, and rejects alternatives.
        """
        action = await self.db.get(AgentAction, action_id)
        if not action or action.status != "PENDING":
            return None

        # 1. Update action status to APPROVED
        action.status = "APPROVED"
        action.approved_at = func.now()

        # 2. Automatically reject other alternative plans for the same source_issue
        stmt_reject = update(AgentAction).where(
            and_(
                AgentAction.source_issue == action.source_issue,
                AgentAction.id != action_id,
                AgentAction.status == "PENDING"
            )
        ).values(status="REJECTED")
        await self.db.execute(stmt_reject)

        # 3. Create Audit Log record
        audit = AuditLog(
            user_id=user_id,
            event_type="AGENT_ACTION_APPROVED",
            details={
                "action_id": action.id,
                "title": action.title,
                "action_type": action.action_type,
                "source_issue": action.source_issue
            }
        )
        self.db.add(audit)
        await self.db.commit()

        # 4. Trigger execution
        # Running execution logic and saving execution stats (completed / failed)
        await self.executor.execute_action(action)
        return action

    async def reject_action(self, action_id: int, user_id: int | None = None) -> AgentAction | None:
        """
        Rejects a proposed action, logging it to the system audit.
        """
        action = await self.db.get(AgentAction, action_id)
        if not action or action.status != "PENDING":
            return None

        action.status = "REJECTED"

        # Create Audit Log record
        audit = AuditLog(
            user_id=user_id,
            event_type="AGENT_ACTION_REJECTED",
            details={
                "action_id": action.id,
                "title": action.title,
                "action_type": action.action_type
            }
        )
        self.db.add(audit)
        await self.db.commit()
        return action
