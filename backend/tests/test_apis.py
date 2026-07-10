import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Event, Order, OrderItem, Product, User


@pytest_asyncio.fixture
async def seed_api_data(db_session: AsyncSession) -> None:
    # 1. Users (1 active, 1 soft-deleted)
    user1 = User(
        full_name="Active Customer",
        email="active@example.com",
        password_hash="pw",
        role="customer",
        is_deleted=False,
    )
    user2 = User(
        full_name="Deleted Customer",
        email="deleted@example.com",
        password_hash="pw",
        role="customer",
        is_deleted=True,
    )
    db_session.add_all([user1, user2])
    await db_session.commit()

    # 2. Categories
    cat1 = Category(name="Electronics", slug="electronics", is_deleted=False)
    cat2 = Category(name="Fashion", slug="fashion", is_deleted=True)
    db_session.add_all([cat1, cat2])
    await db_session.commit()

    # 3. Products
    p1 = Product(
        category_id=cat1.id,
        name="Laptop",
        slug="laptop",
        brand="Apple",
        price=Decimal("1200.00"),
        stock=10,
        is_deleted=False,
    )
    p2 = Product(
        category_id=cat1.id,
        name="Mouse",
        slug="mouse",
        brand="Logitech",
        price=Decimal("25.00"),
        stock=0,  # Out of stock
        is_deleted=False,
    )
    p3 = Product(
        category_id=cat1.id,
        name="Old Phone",
        slug="old-phone",
        brand="Samsung",
        price=Decimal("300.00"),
        stock=5,
        is_deleted=True,  # Deleted
    )
    db_session.add_all([p1, p2, p3])
    await db_session.commit()

    # 4. Orders & Items
    order = Order(
        user_id=user1.id,
        status="completed",
        subtotal=Decimal("1200.00"),
        tax=Decimal("96.00"),
        discount=Decimal("0.00"),
        total=Decimal("1296.00"),
    )
    db_session.add(order)
    await db_session.commit()

    item = OrderItem(
        order_id=order.id,
        product_id=p1.id,
        quantity=1,
        unit_price=Decimal("1200.00"),
        subtotal=Decimal("1200.00"),
    )
    db_session.add(item)
    await db_session.commit()

    # 5. Events
    event = Event(
        user_id=user1.id,
        session_id=uuid.uuid4(),
        event_type="view_item",
        page="/products/laptop",
        product_id=p1.id,
        metadata_={"test": True},
    )
    db_session.add(event)
    await db_session.commit()


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_api_data")
async def test_get_users_api(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] == 1  # Soft-deleted user excluded
    assert data["items"][0]["email"] == "active@example.com"


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_api_data")
async def test_get_categories_api(client: AsyncClient) -> None:
    response = await client.get("/api/v1/categories")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1  # Soft-deleted category excluded
    assert data["items"][0]["slug"] == "electronics"


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_api_data")
async def test_get_products_api(client: AsyncClient) -> None:
    # Test active products fetch
    response = await client.get("/api/v1/products")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2  # Laptop and Mouse (Old Phone is deleted)

    # Test search query
    search_res = await client.get("/api/v1/products?search=Laptop")
    assert search_res.status_code == 200
    assert search_res.json()["total"] == 1
    assert search_res.json()["items"][0]["name"] == "Laptop"

    # Test filtering in_stock=false
    stock_res = await client.get("/api/v1/products?in_stock=false")
    assert stock_res.status_code == 200
    assert stock_res.json()["total"] == 1
    assert stock_res.json()["items"][0]["name"] == "Mouse"

    # Test price sorting (descending)
    sort_res = await client.get("/api/v1/products?sort_by=price&sort_order=desc")
    assert sort_res.status_code == 200
    items = sort_res.json()["items"]
    assert float(items[0]["price"]) == 1200.00
    assert float(items[1]["price"]) == 25.00


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_api_data")
async def test_get_orders_api(client: AsyncClient) -> None:
    response = await client.get("/api/v1/orders")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"][0]["items"]) == 1
    assert float(data["items"][0]["total"]) == 1296.00


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_api_data")
async def test_get_events_api(client: AsyncClient) -> None:
    response = await client.get("/api/v1/events")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["event_type"] == "view_item"
    assert data["items"][0]["metadata"]["test"] is True
