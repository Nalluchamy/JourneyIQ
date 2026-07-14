import pytest
import datetime
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models import Category, Product, User, Order
from app.services.copilot.conversation_memory import copilot_memory
from app.services.copilot.query_engine import CopilotQueryEngine
from app.services.copilot.report_generator import CopilotReportGenerator
from app.services.copilot.insight_engine import CopilotInsightEngine
from app.services.copilot.executive_summary import CopilotExecutiveSummary


@pytest.mark.asyncio
async def test_conversation_memory():
    session_id = "test-session-123"
    
    # Init context
    context = copilot_memory.get_session_context(session_id)
    assert context["preferred_report_type"] == "weekly"
    assert len(context["previous_questions"]) == 0

    # Record questions
    copilot_memory.record_question(session_id, "Why did revenue decrease?")
    context = copilot_memory.get_session_context(session_id)
    assert len(context["previous_questions"]) == 1
    assert context["previous_questions"][0] == "Why did revenue decrease?"

    # Update context parameters
    copilot_memory.update_session_context(session_id, {"business_focus": "revenue"})
    context = copilot_memory.get_session_context(session_id)
    assert context["business_focus"] == "revenue"

    # Reset
    copilot_memory.clear_session(session_id)
    assert len(copilot_memory.get_session_context(session_id)["previous_questions"]) == 0


@pytest.mark.asyncio
async def test_query_engine(db_session: AsyncSession):
    # Seed Category & Product
    category = Category(name="Electronics", slug="electronics")
    db_session.add(category)
    await db_session.flush()

    prod = Product(
        category_id=category.id,
        name="Voyager Power Cell",
        slug="voyager-cell",
        brand="Voyager",
        price=Decimal("49.99"),
        stock=2,
        is_active=True
    )
    db_session.add(prod)
    await db_session.commit()

    engine = CopilotQueryEngine(db_session)
    
    # Test revenue drop intent classification
    res_rev = await engine.execute_query("Why did revenue decrease this week?")
    assert res_rev["intent"] == "REVENUE_DROP"
    assert "revenue_drop_pct" in res_rev["data"]
    assert "Orders" in res_rev["sources"]

    # Test inventory restock intent
    res_stock = await engine.execute_query("Which products should I restock?")
    assert res_stock["intent"] == "INVENTORY_RESTOCK"
    assert "low_stock_count" in res_stock["data"]
    assert res_stock["data"]["low_stock_count"] > 0

    # Test CSAT sentiment intent
    res_csat = await engine.execute_query("How is customer satisfaction?")
    assert res_csat["intent"] == "CUSTOMER_SATISFACTION"
    assert "satisfaction_score" in res_csat["data"]


@pytest.mark.asyncio
async def test_insight_engine(db_session: AsyncSession):
    # Seed Category & Product (to trigger inventory low stock)
    category = Category(name="Electronics", slug="electronics")
    db_session.add(category)
    await db_session.flush()

    prod = Product(
        category_id=category.id,
        name="Voyager Power Cell",
        slug="voyager-cell",
        brand="Voyager",
        price=Decimal("49.99"),
        stock=2,
        is_active=True
    )
    db_session.add(prod)
    await db_session.commit()

    engine = CopilotInsightEngine(db_session)
    insights = await engine.generate_business_insights()
    assert len(insights) > 0
    assert "type" in insights[0]

    risks = await engine.get_business_risks()
    assert isinstance(risks, list)

    score = await engine.calculate_business_risk_score()
    assert 0 <= score <= 100


@pytest.mark.asyncio
async def test_report_generator(db_session: AsyncSession):
    generator = CopilotReportGenerator(db_session)
    
    # JSON report check
    json_data = await generator.generate_report_data("weekly")
    assert json_data["type"] == "weekly"
    assert "summary" in json_data
    assert "risks_and_actions" in json_data

    # Markdown report formatting check
    md_text = await generator.generate_markdown_report("daily")
    assert "Daily Business Executive Report" in md_text
    assert "Executive Sales Summary" in md_text


@pytest.mark.asyncio
async def test_copilot_endpoints_router(client: AsyncClient, db_session: AsyncSession):
    from unittest.mock import patch
    
    # Create an admin user to access endpoints
    admin_user = User(
        email="admin@example.com",
        password_hash="hash",
        full_name="Admin Owner",
        role="admin",
        is_verified=True,
    )
    # Seed Product to ensure query engine does not return empty sets
    category = Category(name="Electronics", slug="electronics")
    db_session.add_all([admin_user, category])
    await db_session.flush()

    prod = Product(
        category_id=category.id,
        name="Voyager Power Cell",
        slug="voyager-cell",
        brand="Voyager",
        price=Decimal("49.99"),
        stock=2,
        is_active=True
    )
    db_session.add(prod)
    await db_session.commit()

    token = create_access_token(admin_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # Test suggestions question endpoint
    res_q = await client.get("/api/v1/copilot/questions", headers=headers)
    assert res_q.status_code == 200
    assert len(res_q.json()["data"]) > 0

    # Test dashboard summary metrics endpoint
    res_sum = await client.get("/api/v1/copilot/summary", headers=headers)
    assert res_sum.status_code == 200
    assert "kpi_cards" in res_sum.json()["data"]
    assert "business_risks" in res_sum.json()["data"]

    # Test report compiling endpoint
    res_rep = await client.get("/api/v1/copilot/report/weekly?format=markdown", headers=headers)
    assert res_rep.status_code == 200
    assert "report" in res_rep.json()["data"]

    # Test copilot chat interaction
    payload = {
        "message": "Why did revenue decrease this week?",
        "session_id": "test-session-999"
    }
    
    # Use patches to ensure LLMs are treated as unconfigured (forces fallback branch)
    with patch("app.services.assistant.providers.nvidia.NvidiaAIProvider.is_configured", return_value=False), \
         patch("app.services.assistant.providers.gemini.GeminiAIProvider.is_configured", return_value=False), \
         patch("app.services.assistant.providers.openai.OpenAIProvider.is_configured", return_value=False):
        res_chat = await client.post("/api/v1/copilot/chat", json=payload, headers=headers)
        
    assert res_chat.status_code == 200
    data = res_chat.json()["data"]
    assert "observation" in data
    assert "evidence" in data
    assert "explanation" in data
    assert "recommendation" in data
    assert "confidence" in data
    assert data["confidence"] > 0
