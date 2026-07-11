import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agent.orchestrator import AgentOrchestrator
from app.services.agent.safety import agent_safety
from app.services.agent.memory import agent_memory
from app.services.agent.learning import agent_learning


@pytest.mark.asyncio
async def test_agent_orchestration_loop(db_session: AsyncSession) -> None:
    """Verify that agent orchestrator runs its stages and collects anomalies/plans."""
    orchestrator = AgentOrchestrator(db_session)
    status = await orchestrator.get_orchestrator_status()
    
    assert "status" in status
    assert "state" in status
    assert "observations" in status
    assert "findings" in status
    assert "proposed_plans" in status
    assert "learning_statistics" in status


def test_agent_safety_queue() -> None:
    """Verify pending actions can be approved or rejected with safety guardrails."""
    # Ensure items exist in queue
    pending = agent_safety.get_pending()
    assert len(pending) > 0
    
    action_id = pending[0]["id"]
    
    # Test approval
    approved = agent_safety.approve_action(action_id)
    assert approved is not None
    assert approved["status"] == "approved"
    
    # Test non-existent approval
    invalid = agent_safety.approve_action("fake-id")
    assert invalid is None


def test_agent_learning_evaluation() -> None:
    """Verify learning stats return conversion lifts and saved metrics."""
    stats = agent_learning.compile_learning_statistics()
    assert "conversion_lift_pct" in stats
    assert "recovered_revenue" in stats
    assert stats["conversion_lift_pct"] > 0


@pytest.mark.asyncio
async def test_agent_api_endpoints(client: AsyncClient) -> None:
    """Verify HTTP GET & POST endpoints for Agent status, history, and approval actions."""
    # 1. Get status
    s_res = await client.get("/api/v1/agent/status")
    assert s_res.status_code == 200
    assert s_res.json()["success"] is True

    # 2. Get history
    h_res = await client.get("/api/v1/agent/history")
    assert h_res.status_code == 200
    assert h_res.json()["success"] is True

    # 3. Get pending queue
    p_res = await client.get("/api/v1/agent/pending")
    assert p_res.status_code == 200
    assert p_res.json()["success"] is True
    
    # If there is a pending action, try approving it
    pending_list = p_res.json()["data"]
    if pending_list:
        action_id = pending_list[0]["id"]
        app_res = await client.post(f"/api/v1/agent/actions/{action_id}/approve")
        assert app_res.status_code == 200
        assert app_res.json()["success"] is True
