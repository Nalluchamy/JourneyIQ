import pytest
from httpx import AsyncClient
from app.services.generative.marketing_generator import marketing_generator
from app.services.generative.layout_generator import layout_generator
from app.services.generative.customer_journey_simulator import journey_simulator
from app.services.generative.image_prompt_generator import image_prompt_generator


@pytest.mark.asyncio
async def test_marketing_generation() -> None:
    """Verify segment marketing campaign returns subject and body."""
    res = await marketing_generator.generate_campaign(
        segment="VIP Customers",
        campaign_type="email",
        product_context="Running shoes"
    )
    assert "subject" in res
    assert "body" in res
    assert "VIP" in res["subject"] or "VIP" in res["body"] or len(res["subject"]) > 0


def test_layout_generation() -> None:
    """Verify storefront layout suggest theme configs."""
    res = layout_generator.generate_layout("VIP Customers")
    assert "hero_layout" in res
    assert "primary_color" in res
    assert "#" in res["primary_color"]


def test_journey_simulation() -> None:
    """Verify simulation calculates lifts and drop-offs."""
    res = journey_simulator.simulate_journey("At Risk Customers")
    assert "current_journey" in res
    assert "optimized_journey" in res
    assert res["conversion_lift_pct"] > 0.0
    assert len(res["drop_off_points"]) > 0


def test_image_prompt_generation() -> None:
    """Verify prompt constructor builds detailed visual guides."""
    res = image_prompt_generator.generate_prompt(
        style="cyberpunk",
        product_context="Hydro Flask",
        colors=["purple", "cyan"]
    )
    assert "cyberpunk" in res["style"]
    assert "purple" in res["generated_prompt"]


@pytest.mark.asyncio
async def test_generative_api_routes(client: AsyncClient) -> None:
    """Verify HTTP post routes for all generative AI endpoints."""
    # 1. Marketing Copy
    m_res = await client.post("/api/v1/generative/marketing", json={
        "segment": "New Customers",
        "campaign_type": "sms",
        "product_context": "Backpack"
    })
    assert m_res.status_code == 200
    assert m_res.json()["success"] is True

    # 2. Theme Layout
    l_res = await client.post("/api/v1/generative/layout", json={
        "segment": "VIP Customers"
    })
    assert l_res.status_code == 200
    assert l_res.json()["success"] is True

    # 3. Journey Sim
    j_res = await client.post("/api/v1/generative/journey", json={
        "segment": "General Visitors"
    })
    assert j_res.status_code == 200
    assert j_res.json()["success"] is True

    # 4. Image Prompt
    i_res = await client.post("/api/v1/generative/image-prompt", json={
        "style": "minimalist",
        "product_context": "Vase",
        "colors": ["white", "grey"]
    })
    assert i_res.status_code == 200
    assert i_res.json()["success"] is True
