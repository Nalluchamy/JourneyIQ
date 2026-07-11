import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.assistant.intent_classifier import IntentClassifier
from app.services.assistant.memory import assistant_memory


def test_intent_classification() -> None:
    """Verify that intent classifier correctly maps queries to supported intents."""
    classifier = IntentClassifier()
    
    assert classifier.classify("recommend a nice running shoe") == "recommend_product"
    assert classifier.classify("is item A better than item B?") == "compare_products"
    assert classifier.classify("show products under $50") == "price_filter"
    assert classifier.classify("where is my order status?") == "order_status"
    assert classifier.classify("trending products this week") == "trending_products"
    assert classifier.classify("hello there") == "general_qna"


def test_session_memory() -> None:
    """Verify session-only memory context updates correctly."""
    session_id = "test-session-123"
    
    # Init context
    ctx = assistant_memory.get_context(session_id)
    assert ctx["budget"] is None
    
    # Update context
    assistant_memory.update_context(session_id, {"budget": 150.0})
    ctx = assistant_memory.get_context(session_id)
    assert ctx["budget"] == 150.0
    
    # Clear context
    assistant_memory.clear_context(session_id)
    ctx = assistant_memory.get_context(session_id)
    assert ctx["budget"] is None


@pytest.mark.asyncio
async def test_assistant_endpoints(client: AsyncClient) -> None:
    """Verify chatbot chat post and suggestions autocomplete routes."""
    # Test chat suggestions
    sug_res = await client.get("/api/v1/assistant/suggestions")
    assert sug_res.status_code == 200
    assert sug_res.json()["success"] is True
    assert len(sug_res.json()["data"]["suggestions"]) > 0

    # Test chatbot query
    chat_res = await client.post(
        "/api/v1/assistant/chat",
        json={"message": "Recommend a laptop under $1000", "session_id": "test-session-api"}
    )
    assert chat_res.status_code == 200
    assert chat_res.json()["success"] is True
    assert "reply" in chat_res.json()["data"]
    assert "source" in chat_res.json()["data"]
