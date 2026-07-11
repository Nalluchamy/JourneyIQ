from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models import Category, Coupon, Product, User
from app.utils.sanitization import sanitize_input


@pytest_asyncio.fixture
async def seed_boost_data(db_session: AsyncSession) -> dict:
    """Seeds rich fixtures for testing stateful checkout and catalog actions."""
    # 1. Categories and Products
    cat = Category(name="Electronics", slug="electronics")
    db_session.add(cat)
    await db_session.commit()

    prod = Product(
        category_id=cat.id,
        name="Smartphone X",
        slug="smartphone-x",
        brand="BrandY",
        price=Decimal("799.99"),
        stock=15,
        is_deleted=False,
    )
    db_session.add(prod)

    # 2. Coupon
    import datetime
    now = datetime.datetime.now(datetime.UTC)
    coupon = Coupon(
        code="SAVE10",
        discount_type="percentage",
        discount_value=Decimal("10.00"),
        is_active=True,
        minimum_order=Decimal("100.00"),
        start_date=now - datetime.timedelta(days=1),
        expiry_date=now + datetime.timedelta(days=10)
    )
    db_session.add(coupon)
    await db_session.commit()

    # 3. User & Auth Token
    user = User(
        full_name="Testing Customer",
        email="test_cust@example.com",
        password_hash="hashed_pw",
        role="customer",
        is_deleted=False,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(prod)

    # Seed completed order for reviews verified purchaser constraint check
    from app.models.order import Order
    from app.models.order_item import OrderItem
    order = Order(
        user_id=user.id,
        status="completed",
        subtotal=Decimal("799.99"),
        tax=Decimal("0.00"),
        discount=Decimal("0.00"),
        total=Decimal("799.99"),
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    order_item = OrderItem(
        order_id=order.id,
        product_id=prod.id,
        quantity=1,
        unit_price=Decimal("799.99"),
        subtotal=Decimal("799.99")
    )
    db_session.add(order_item)
    await db_session.commit()

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    return {
        "user": user,
        "token": token,
        "headers": headers,
        "product": prod,
        "coupon": coupon
    }


@pytest.mark.anyio
@pytest.mark.usefixtures("init_db")
async def test_input_sanitization() -> None:
    """Verify that script elements and raw HTML are stripped correctly."""
    dirty = "<script>alert('xss')</script>Hello <b>World</b>"
    clean = sanitize_input(dirty)
    assert clean == "Hello World"

    assert sanitize_input(123) == 123
    assert sanitize_input(None) is None


@pytest.mark.anyio
async def test_auth_validation_errors(client: AsyncClient) -> None:
    """Exercises error conditions in registration and login flows."""
    # Duplicate email check setup
    reg_payload = {
        "email": "invalid-email-format",
        "password": "short",
        "full_name": "Test Formats"
    }
    # Expect validation error 422 for format issues
    res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 422


@pytest.mark.anyio
async def test_profile_endpoints(client: AsyncClient, seed_boost_data: dict) -> None:
    """Tests viewing and updating user profiles."""
    headers = seed_boost_data["headers"]

    # Get profile
    res = await client.get("/api/v1/users/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["email"] == "test_cust@example.com"

    # Update profile
    update_payload = {"full_name": "Updated Customer Name"}
    res = await client.patch("/api/v1/users/me", json=update_payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["full_name"] == "Updated Customer Name"


@pytest.mark.anyio
async def test_cart_operations(client: AsyncClient, seed_boost_data: dict) -> None:
    """Exercises full cart life cycle: Add, Update, List, Delete, Clear."""
    headers = seed_boost_data["headers"]
    prod = seed_boost_data["product"]

    # 1. Add item to cart
    res = await client.post(
        "/api/v1/cart",
        json={"product_id": prod.id, "quantity": 2},
        headers=headers
    )
    assert res.status_code == 201

    # 2. Get cart items list
    res = await client.get("/api/v1/cart", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1
    assert res.json()["data"][0]["quantity"] == 2

    # 3. Update cart item quantity
    res = await client.put(
        f"/api/v1/cart/{prod.id}",
        json={"quantity": 5},
        headers=headers
    )
    assert res.status_code == 200

    # 4. Delete item
    res = await client.delete(f"/api/v1/cart/{prod.id}", headers=headers)
    assert res.status_code == 200

    # 5. Clear cart
    res = await client.delete("/api/v1/cart", headers=headers)
    assert res.status_code == 200


@pytest.mark.anyio
async def test_wishlist_operations(client: AsyncClient, seed_boost_data: dict) -> None:
    """Exercises wishlist addition and deletion operations."""
    headers = seed_boost_data["headers"]
    prod = seed_boost_data["product"]

    # 1. Add to wishlist
    res = await client.post("/api/v1/wishlist", json={"product_id": prod.id}, headers=headers)
    assert res.status_code == 201

    # 2. Get wishlist
    res = await client.get("/api/v1/wishlist", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1

    # 3. Delete from wishlist
    res = await client.delete(f"/api/v1/wishlist/{prod.id}", headers=headers)
    assert res.status_code == 200


@pytest.mark.anyio
async def test_address_management(client: AsyncClient, seed_boost_data: dict) -> None:
    """Verifies adding and updating customer shipping addresses."""
    headers = seed_boost_data["headers"]

    addr_payload = {
        "full_name": "John Tester",
        "phone": "9876543210",
        "address_line1": "123 Main St",
        "city": "Dallas",
        "state": "TX",
        "postal_code": "75001",
        "country": "USA",
        "is_default": True
    }

    # 1. Create Address
    res = await client.post("/api/v1/addresses", json=addr_payload, headers=headers)
    assert res.status_code == 201
    addr_id = res.json()["id"]

    # 2. List Addresses
    res = await client.get("/api/v1/addresses", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 3. Update Address
    res = await client.put(
        f"/api/v1/addresses/{addr_id}",
        json={**addr_payload, "city": "Houston"},
        headers=headers
    )
    assert res.status_code == 200
    assert res.json()["city"] == "Houston"

    # 4. Delete Address
    res = await client.delete(f"/api/v1/addresses/{addr_id}", headers=headers)
    assert res.status_code == 204


@pytest.mark.anyio
async def test_reviews_endpoints(client: AsyncClient, seed_boost_data: dict) -> None:
    """Tests submitting product reviews and retrieving them."""
    headers = seed_boost_data["headers"]
    prod = seed_boost_data["product"]

    review_payload = {
        "rating": 5,
        "review": "Outstanding smartphone!"
    }

    # 1. Submit Review
    res = await client.post(
        f"/api/v1/products/{prod.id}/reviews",
        json=review_payload,
        headers=headers
    )
    assert res.status_code == 201

    # 2. Get reviews
    res = await client.get(f"/api/v1/products/{prod.id}/reviews")
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1
    assert res.json()["data"][0]["review"] == "Outstanding smartphone!"
