import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.category import Category
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User


@pytest.mark.asyncio
async def test_reviews_verification_and_crud(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # 1. Create user, category, and product
    user = User(
        email="reviewer@example.com",
        password_hash="pw",
        full_name="Reviewer User",
        role="customer",
        is_verified=True,
    )
    category = Category(name="Reviews Test Category", slug="reviews-test-category")
    db_session.add(category)
    await db_session.flush()

    product = Product(
        category_id=category.id,
        name="Review Test Product",
        slug="review-test-product",
        price=19.99,
        stock=5,
        is_active=True,
    )
    db_session.add_all([user, product])
    await db_session.commit()

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Attempt to create review without purchasing -> should fail with 400
    review_payload = {"rating": 5, "review": "Loved it!"}
    res_fail = await client.post(
        f"/api/v1/products/{product.id}/reviews", json=review_payload, headers=headers
    )
    assert res_fail.status_code == 400
    assert "only verified purchasers" in res_fail.json()["message"].lower()

    # 3. Create a completed order in database containing the product
    order = Order(
        user_id=user.id,
        status="completed",
        subtotal=19.99,
        tax=1.60,
        discount=0.00,
        total=21.59,
    )
    db_session.add(order)
    await db_session.flush()

    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=1,
        unit_price=19.99,
        subtotal=19.99,
    )
    db_session.add(order_item)
    await db_session.commit()

    # 4. Attempt review again after purchase -> should succeed (201 Created)
    res_ok = await client.post(
        f"/api/v1/products/{product.id}/reviews", json=review_payload, headers=headers
    )
    assert res_ok.status_code == 201
    review_data = res_ok.json()
    assert review_data["success"] is True
    assert review_data["data"]["rating"] == 5
    assert review_data["data"]["review"] == "Loved it!"
    review_id = review_data["data"]["id"]

    # 5. Fetch reviews for the product
    get_res = await client.get(f"/api/v1/products/{product.id}/reviews")
    assert get_res.status_code == 200
    assert len(get_res.json()["data"]) == 1
    assert get_res.json()["data"][0]["id"] == review_id

    # 6. Update review
    update_payload = {"rating": 4, "review": "Actually, it was decent."}
    put_res = await client.patch(
        f"/api/v1/reviews/{review_id}", json=update_payload, headers=headers
    )
    assert put_res.status_code == 200
    assert put_res.json()["data"]["rating"] == 4

    # 7. Delete review
    del_res = await client.delete(f"/api/v1/reviews/{review_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True
