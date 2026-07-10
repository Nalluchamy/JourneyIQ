from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.user import User
from app.models.category import Category


@pytest.mark.asyncio
async def test_cart_crud_operations(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # 1. Create a customer user, a category, and a product
    user = User(
        email="cart_user@example.com",
        password_hash="pw",
        full_name="Cart User",
        role="customer",
        is_verified=True,
    )
    category = Category(name="Cart Test Category", slug="cart-test-category")
    db_session.add(category)
    await db_session.flush()

    product = Product(
        category_id=category.id,
        name="Cart Test Product",
        slug="cart-test-product",
        price=10.99,
        stock=10,
        is_active=True,
    )
    db_session.add_all([user, product])
    await db_session.commit()

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}", "x-session-id": "11111111-2222-3333-4444-555555555555"}

    # 2. Add product to cart
    payload = {"product_id": product.id, "quantity": 2}
    response = await client.post("/api/v1/cart", json=payload, headers=headers)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["quantity"] == 2
    assert res_data["data"]["product_id"] == product.id

    # 3. Add again (should increment quantity to 4)
    response_inc = await client.post("/api/v1/cart", json=payload, headers=headers)
    assert response_inc.status_code == 201
    assert response_inc.json()["data"]["quantity"] == 4

    # 4. Get cart items
    get_res = await client.get("/api/v1/cart", headers=headers)
    assert get_res.status_code == 200
    assert len(get_res.json()["data"]) == 1
    assert get_res.json()["data"][0]["quantity"] == 4

    # 5. Update quantity (setting to 5, which is under stock limit of 10)
    update_res = await client.put(
        f"/api/v1/cart/{product.id}", json={"quantity": 5}, headers=headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["quantity"] == 5

    # 6. Update quantity exceeding stock limit -> should return 400
    exceed_res = await client.put(
        f"/api/v1/cart/{product.id}", json={"quantity": 11}, headers=headers
    )
    assert exceed_res.status_code == 400

    # 7. Remove item from cart
    del_res = await client.delete(f"/api/v1/cart/{product.id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Check cart is empty
    empty_res = await client.get("/api/v1/cart", headers=headers)
    assert len(empty_res.json()["data"]) == 0
