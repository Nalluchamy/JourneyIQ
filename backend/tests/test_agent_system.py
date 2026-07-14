import pytest
import datetime
from httpx import AsyncClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_action import AgentAction
from app.models.agent_learning import AgentLearning
from app.models.product import Product
from app.models.category import Category
from app.services.agent.observer import ObserverModule
from app.services.agent.analyzer import AnalyzerModule
from app.services.agent.planner import PlannerModule
from app.services.agent.approval import ApprovalModule
from app.services.agent.executor import ExecutorModule
from app.services.agent.learner import LearnerModule


@pytest.mark.asyncio
async def test_observer_module(db_session: AsyncSession) -> None:
    """Test that observer queries the database and fetches e-commerce metrics correctly."""
    observer = ObserverModule(db_session)
    obs = await observer.observe_environment()
    
    assert "inventory" in obs
    assert "orders" in obs
    assert "revenue" in obs
    assert "customers" in obs
    assert "reviews" in obs
    assert "cart" in obs
    assert "events" in obs


@pytest.mark.asyncio
async def test_analyzer_and_planner_modules(db_session: AsyncSession) -> None:
    """Test that analyzer raises issues and planner generates actions in database."""
    # 1. Setup mock observation with out of stock
    obs = {
        "inventory": {
            "total_products": 10,
            "low_stock_count": 1,
            "low_stock_products": ["Voyager Laptop"],
            "out_of_stock_count": 1,
            "out_of_stock_products": ["Nike Shoes"],
        },
        "revenue": {
            "today": 100.0,
            "yesterday": 200.0,
            "drop_pct": 50.0,
        },
        "payments": {
            "payment_failure_rate": 15.0
        }
    }
    
    analyzer = AnalyzerModule()
    issues = analyzer.analyze_observations(obs)
    
    # Assert issues raised
    issue_types = [i["issue_type"] for i in issues]
    assert "REVENUE_DROP" in issue_types
    assert "OUT_OF_STOCK" in issue_types
    
    # 2. Planner converts issues
    planner = PlannerModule(db_session)
    actions = await planner.construct_plans(issues)
    assert len(actions) > 0
    
    # Verify saved actions in DB
    stmt = select(AgentAction).where(AgentAction.status == "PENDING")
    res = await db_session.execute(stmt)
    db_actions = res.scalars().all()
    assert len(db_actions) > 0


@pytest.mark.asyncio
async def test_approval_and_executor_modules(db_session: AsyncSession) -> None:
    """Test that approving an action triggers execution and automatically rejects alternative actions."""
    # 1. Setup category and product for restocking test
    category = Category(name="Electronics", slug="electronics")
    db_session.add(category)
    await db_session.commit()
    
    product = Product(
        category_id=category.id,
        name="Voyager Laptop",
        slug="voyager-laptop",
        price=1200.0,
        stock=2,
        is_active=True
    )
    db_session.add(product)
    await db_session.commit()

    # 2. Create pending actions with the same source issue
    action_1 = AgentAction(
        action_type="RESTOCK",
        title="Emergency restock Voyager Laptop",
        description="Replenish stock for Voyager Laptop",
        priority="HIGH",
        status="PENDING",
        source_issue="LOW_STOCK-2026-07-13",
        confidence=0.95
    )
    action_2 = AgentAction(
        action_type="NOTIFICATION",
        title="Alert warehouse on stockout",
        description="Notify warehouse about stockout",
        priority="HIGH",
        status="PENDING",
        source_issue="LOW_STOCK-2026-07-13",
        confidence=0.85
    )
    db_session.add(action_1)
    db_session.add(action_2)
    await db_session.commit()

    # 3. Approve action_1
    approval = ApprovalModule(db_session)
    approved = await approval.approve_action(action_1.id)
    assert approved is not None
    assert approved.status == "COMPLETED"

    # Refresh items from DB
    await db_session.refresh(action_1)
    await db_session.refresh(action_2)
    await db_session.refresh(product)

    # Assert action_1 is completed, product stock is updated, and action_2 is automatically rejected
    assert action_1.status == "COMPLETED"
    assert product.stock == 22
    assert action_2.status == "REJECTED"


@pytest.mark.asyncio
async def test_learner_evaluation(db_session: AsyncSession) -> None:
    """Test that learner module computes pre/post metrics and logs ROI learnings."""
    action = AgentAction(
        action_type="COUPON",
        title="Flash sale coupon",
        description="Create flash coupon",
        priority="CRITICAL",
        status="APPROVED",
        source_issue="REVENUE_DROP",
        confidence=0.90,
        executed_at=func.now(),
        execution_time_ms=120
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    learner = LearnerModule(db_session)
    learning = await learner.evaluate_action_outcome(action)
    assert learning is not None
    assert learning.action_id == action.id
    assert learning.roi > 0.0

    summary = await learner.get_summary_statistics()
    assert "average_roi" in summary
    assert "conversion_lift_pct" in summary


@pytest.mark.asyncio
async def test_agent_endpoints(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test FastAPIs for orchestrator run loops, action lists, approvals, and history logs."""
    # Seed Category & Product to trigger LOW_STOCK anomaly
    category = Category(name="Electronics", slug="electronics")
    db_session.add(category)
    await db_session.flush()
    
    product = Product(
        category_id=category.id,
        name="Voyager Laptop",
        slug="voyager-laptop",
        price=1200.0,
        stock=2,
        is_active=True
    )
    db_session.add(product)
    await db_session.commit()

    # 1. Run orchestrator loop via API
    run_res = await client.post("/api/v1/agent/run")
    assert run_res.status_code == 200
    assert run_res.json()["success"] is True

    # 2. Get status API
    status_res = await client.get("/api/v1/agent/status")
    assert status_res.status_code == 200
    assert status_res.json()["success"] is True
    
    # 3. Get actions list API
    actions_res = await client.get("/api/v1/agent/actions")
    assert actions_res.status_code == 200
    assert actions_res.json()["success"] is True
    assert len(actions_res.json()["data"]) > 0

    # 4. Get logs API
    logs_res = await client.get("/api/v1/agent/logs")
    assert logs_res.status_code == 200
    assert logs_res.json()["success"] is True

    # 5. Get learning API
    learning_res = await client.get("/api/v1/agent/learning")
    assert learning_res.status_code == 200
    assert learning_res.json()["success"] is True
