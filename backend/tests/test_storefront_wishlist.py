import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.product import Product
from app.models.user import User
from app.models.category import Category


@pytest.mark.asyncio
async def test_wishlist_crud_operations(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # 1. Create a customer user, a category, and a product
    user = User(
        email="wish_user@example.com",
        password_hash="pw",
        full_name="Wish User",
        role="customer",
        is_verified=True,
    )
    category = Category(name="Wish Test Category", slug="wish-test-category")
    db_session.add(category)
    await db_session.flush()

    product = Product(
        category_id=category.id,
        name="Wishlist Test Product",
        slug="wishlist-test-product",
        price=15.99,
        stock=5,
        is_active=True,
    )
    db_session.add_all([user, product])
    await db_session.commit()

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}", "x-session-id": "22222222-3333-4444-5555-666666666666"}

    # 2. Add product to wishlist
    payload = {"product_id": product.id}
    response = await client.post("/api/v1/wishlist", json=payload, headers=headers)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["product_id"] == product.id

    # 3. Add again (should return success and existing item, avoiding duplicate)
    response_dup = await client.post("/api/v1/wishlist", json=payload, headers=headers)
    assert response_dup.status_code == 201
    assert "already in your wishlist" in response_dup.json()["message"].lower()

    # 4. Get wishlist items
    get_res = await client.get("/api/v1/wishlist", headers=headers)
    assert get_res.status_code == 200
    assert len(get_res.json()["data"]) == 1
    assert get_res.json()["data"][0]["product_id"] == product.id

    # 5. Remove item from wishlist
    del_res = await client.delete(f"/api/v1/wishlist/{product.id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Check wishlist is empty
    empty_res = await client.get("/api/v1/wishlist", headers=headers)
    assert len(empty_res.json()["data"]) == 0
