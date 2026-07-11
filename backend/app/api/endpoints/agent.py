from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.response import APIResponse
from app.services.agent.orchestrator import AgentOrchestrator
from app.services.agent.safety import agent_safety
from app.services.agent.memory import agent_memory
from app.services.agent.execution import agent_executor

router = APIRouter()


@router.get("/status", response_model=APIResponse[dict[str, Any]])
async def get_agent_orchestrator_status(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    """Retrieve active perception findings, plan lists, and metrics summaries."""
    orch = AgentOrchestrator(db)
    res = await orch.get_orchestrator_status()
    return APIResponse(success=True, message="Orchestrator status loaded.", data=res)


@router.get("/history", response_model=APIResponse[list[dict[str, Any]]])
async def get_agent_decision_history() -> Any:
    """Retrieve historic logs of executed/completed decisions."""
    history = agent_memory.get_history()
    return APIResponse(success=True, message="Execution logs loaded.", data=history)


@router.get("/pending", response_model=APIResponse[list[dict[str, Any]]])
async def get_pending_safety_queue() -> Any:
    """Retrieve safety approval queue list."""
    pending = agent_safety.get_pending()
    return APIResponse(success=True, message="Awaiting approvals queue loaded.", data=pending)


@router.post("/actions/{action_id}/approve", response_model=APIResponse[dict[str, Any]])
async def approve_agent_action(
    action_id: str,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    """Approve a pending action and execute it immediately."""
    action = agent_safety.approve_action(action_id)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action ID not found or already processed."
        )
    
    # Run execution
    res = agent_executor.execute_action(action)
    return APIResponse(success=True, message="Action approved and executed successfully.", data=res)


@router.post("/actions/{action_id}/reject", response_model=APIResponse[dict[str, Any]])
async def reject_agent_action(
    action_id: str
) -> Any:
    """Reject and discard a pending action."""
    action = agent_safety.reject_action(action_id)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action ID not found or already processed."
        )
    
    # Write to memory log
    agent_memory.log_rejection(action["title"])
    return APIResponse(
        success=True,
        message="Action rejected and dismissed.",
        data={"action_id": action_id, "status": "rejected"}
    )
