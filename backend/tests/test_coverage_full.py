import pytest
import pytest_asyncio
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Product, User, Coupon, ShippingAddress
from app.core.security import create_access_token, get_password_hash


@pytest_asyncio.fixture
async def seed_full_data(db_session: AsyncSession) -> dict:
    """Seed comprehensive models for checkout and authentication testing."""
    # 1. Active User
    user = User(
        full_name="Coverage User",
        email="cov_user@example.com",
        password_hash=get_password_hash("secure_password"),
        role="customer",
        is_deleted=False,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 2. Product with Stock
    cat = Category(name="Gear", slug="gear")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)

    prod = Product(
        category_id=cat.id,
        name="Climbing Rope",
        slug="rope",
        brand="Petzl",
        price=Decimal("199.99"),
        stock=10,
        is_deleted=False,
        is_active=True
    )
    db_session.add(prod)

    # 3. Address
    addr = ShippingAddress(
        user_id=user.id,
        full_name="Coverage User",
        phone="1234567890",
        address_line1="123 Cov Rd",
        city="Denver",
        state="CO",
        postal_code="80201",
        country="USA",
        is_default=True
    )
    db_session.add(addr)
    await db_session.commit()
    await db_session.refresh(addr)

    # 4. Coupon
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    coupon = Coupon(
        code="OFFER15",
        discount_type="percentage",
        discount_value=Decimal("15.00"),
        is_active=True,
        minimum_order=Decimal("50.00"),
        start_date=now - datetime.timedelta(days=1),
        expiry_date=now + datetime.timedelta(days=5)
    )
    db_session.add(coupon)
    await db_session.commit()

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    return {
        "user": user,
        "token": token,
        "headers": headers,
        "product": prod,
        "address": addr,
        "coupon": coupon
    }


@pytest.mark.anyio
async def test_auth_recovery_and_change(client: AsyncClient, seed_full_data: dict) -> None:
    """Verifies password reset requests, token generation, and updates."""
    headers = seed_full_data["headers"]
    
    # 1. Forgot password
    forgot_payload = {"email": "cov_user@example.com"}
    res = await client.post("/api/v1/auth/forgot-password", json=forgot_payload)
    assert res.status_code == 200

    # 2. Change password
    change_payload = {
        "old_password": "secure_password",
        "new_password": "New_secure_password123!"
    }
    res = await client.post("/api/v1/auth/change-password", json=change_payload, headers=headers)
    assert res.status_code == 200


@pytest.mark.anyio
async def test_checkout_validation_failures(client: AsyncClient, seed_full_data: dict) -> None:
    """Tests checkout validations for stockouts, coupon checks, and address selection."""
    headers = seed_full_data["headers"]
    prod = seed_full_data["product"]
    addr = seed_full_data["address"]

    # 1. Empty checkout validation error (no items in cart)
    checkout_payload = {
        "shipping_address_id": addr.id,
        "coupon_code": None
    }
    res = await client.post("/api/v1/checkout", json=checkout_payload, headers=headers)
    assert res.status_code == 400

    # 2. Add product to cart to test preview with items
    res_cart = await client.post(
        "/api/v1/cart",
        json={"product_id": prod.id, "quantity": 1},
        headers=headers
    )
    assert res_cart.status_code == 201

    # 3. Successful Cart Summary Preview
    res = await client.get("/api/v1/cart/summary", headers=headers)
    assert res.status_code == 200

    # 4. Coupon validation endpoint check
    coupon_payload = {
        "code": "INVALIDCODE",
        "cart_total": 199.99
    }
    res = await client.post("/api/v1/checkout/apply-coupon", json=coupon_payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["is_valid"] is False

    # 5. Place order with valid data
    checkout_payload["coupon_code"] = "OFFER15"
    res = await client.post("/api/v1/checkout", json=checkout_payload, headers=headers)
    assert res.status_code == 200
    assert "order_id" in res.json()
