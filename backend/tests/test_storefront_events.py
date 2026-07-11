import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.product import Product


@pytest.mark.asyncio
async def test_event_tracking_and_recent_views(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # 1. Create category and product
    category = Category(name="Events Test Category", slug="events-test-category")
    db_session.add(category)
    await db_session.flush()

    product = Product(
        category_id=category.id,
        name="Event Test Product",
        slug="event-test-product",
        price=9.99,
        stock=5,
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()

    headers = {"x-session-id": "33333333-4444-5555-6666-777777777777"}

    # 2. Log guest product view event
    payload = {
        "event_type": "product_view",
        "page": f"/products/{product.id}",
        "product_id": product.id,
    }
    post_res = await client.post("/api/v1/events", json=payload, headers=headers)
    assert post_res.status_code == 201
    assert post_res.json()["success"] is True

    # 3. Retrieve guest recent views
    get_res = await client.get(
        f"/api/v1/events/recent-views?session_id={headers['x-session-id']}"
    )
    assert get_res.status_code == 200
    data = get_res.json()["data"]
    assert len(data) == 1
    assert data[0]["product_id"] == product.id
