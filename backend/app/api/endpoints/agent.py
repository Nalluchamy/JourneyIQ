from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.agent_action import AgentAction
from app.models.agent_learning import AgentLearning
from app.schemas.response import APIResponse
from app.services.agent.orchestrator import AgentOrchestrator
from app.services.agent.approval import ApprovalModule
from app.services.agent.learner import LearnerModule
from app.services.agent.memory import AgentMemory

router = APIRouter()


@router.get("/status", response_model=APIResponse[dict[str, Any]])
async def get_agent_orchestrator_status(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    """Retrieve live active perception findings, pending approvals, logs, and metrics summaries."""
    orch = AgentOrchestrator(db)
    res = await orch.get_orchestrator_status()
    return APIResponse(success=True, message="Agent orchestrator status loaded.", data=res)


@router.get("/actions", response_model=APIResponse[list[dict[str, Any]]])
async def get_all_agent_actions(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    """Retrieve the complete list of proposed and active agent actions."""
    stmt = select(AgentAction).order_by(AgentAction.created_at.desc())
    res = await db.execute(stmt)
    actions = res.scalars().all()
    
    data = [
        {
            "id": a.id,
            "action_type": a.action_type,
            "title": a.title,
            "description": a.description,
            "priority": a.priority,
            "status": a.status,
            "source_issue": a.source_issue,
            "confidence": a.confidence,
            "reasoning": a.reasoning,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "approved_at": a.approved_at.isoformat() if a.approved_at else None,
            "executed_at": a.executed_at.isoformat() if a.executed_at else None,
            "execution_time_ms": a.execution_time_ms,
            "error_message": a.error_message,
            "retry_count": a.retry_count,
            "execution_result": a.execution_result
        }
        for a in actions
    ]
    return APIResponse(success=True, message="Agent actions loaded.", data=data)


@router.get("/logs", response_model=APIResponse[list[dict[str, Any]]])
async def get_agent_execution_logs(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    """Retrieve history of executed, completed, or rejected decisions."""
    memory = AgentMemory(db)
    logs = await memory.get_history_logs()
    return APIResponse(success=True, message="Agent decision logs loaded.", data=logs)


@router.get("/learning", response_model=APIResponse[list[dict[str, Any]]])
async def get_agent_learning_history(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    """Retrieve historic ROI evaluation records from learnings database table."""
    stmt = select(AgentLearning).order_by(AgentLearning.created_at.desc())
    res = await db.execute(stmt)
    learnings = res.scalars().all()
    
    data = [
        {
            "id": l.id,
            "action_id": l.action_id,
            "revenue_before": l.revenue_before,
            "revenue_after": l.revenue_after,
            "conversion_before": l.conversion_before,
            "conversion_after": l.conversion_after,
            "roi": l.roi,
            "confidence": l.confidence,
            "success": l.success,
            "execution_time_ms": l.execution_time_ms,
            "created_at": l.created_at.isoformat() if l.created_at else None
        }
        for l in learnings
    ]
    return APIResponse(success=True, message="Agent learning history loaded.", data=data)


@router.post("/actions/{action_id}/approve", response_model=APIResponse[dict[str, Any]])
async def approve_agent_action(
    action_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    """Approve a proposed agent action, trigger execution, and reject matching alternatives."""
    approval_service = ApprovalModule(db)
    action = await approval_service.approve_action(action_id)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action ID not found, not in PENDING state, or already processed."
        )
    
    # Calculate learning outcome post-execution
    learner = LearnerModule(db)
    await learner.evaluate_action_outcome(action)

    return APIResponse(
        success=True, 
        message="Action approved and executed successfully.", 
        data={
            "id": action.id,
            "status": action.status,
            "execution_result": action.execution_result,
            "execution_time_ms": action.execution_time_ms
        }
    )


@router.post("/actions/{action_id}/reject", response_model=APIResponse[dict[str, Any]])
async def reject_agent_action(
    action_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    """Reject and discard a proposed agent action."""
    approval_service = ApprovalModule(db)
    action = await approval_service.reject_action(action_id)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action ID not found, not in PENDING state, or already processed."
        )
    
    return APIResponse(
        success=True,
        message="Action rejected and dismissed.",
        data={"id": action_id, "status": "rejected"}
    )


@router.post("/run", response_model=APIResponse[list[dict[str, Any]]])
async def trigger_agent_run_loop(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    """Force an immediate, on-demand execution of the Agent perception-reasoning-planning loop."""
    orch = AgentOrchestrator(db)
    actions = await orch.run_orchestrator_loop()
    return APIResponse(success=True, message="Agent loop run executed.", data=actions)
