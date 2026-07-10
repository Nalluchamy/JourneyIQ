from typing import Any
from unittest.mock import patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import seed
from app.models import Category, Event, Order, Product, Review, User


class MockSessionMaker:
    """Mock context manager for SQLAlchemy sessionmaker in tests."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def __call__(self) -> "MockSessionMaker":
        return self

    async def __aenter__(self) -> AsyncSession:
        return self.session

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass


@pytest.mark.asyncio
async def test_seed_script_execution(db_session: AsyncSession) -> None:
    # Patch AsyncSessionLocal inside seed module to use the test SQLite db_session
    mock_session_maker = MockSessionMaker(db_session)

    with patch("seed.AsyncSessionLocal", mock_session_maker):
        await seed.seed_database()

    # Query counts to verify Faker data generation
    users_total = (await db_session.execute(select(func.count(User.id)))).scalar()
    categories_total = (
        await db_session.execute(select(func.count(Category.id)))
    ).scalar()
    products_total = (await db_session.execute(select(func.count(Product.id)))).scalar()
    orders_total = (await db_session.execute(select(func.count(Order.id)))).scalar()
    reviews_total = (await db_session.execute(select(func.count(Review.id)))).scalar()
    events_total = (await db_session.execute(select(func.count(Event.id)))).scalar()

    # Validate seed dataset metrics
    assert users_total == 100
    assert categories_total == 15
    assert products_total == 100
    assert orders_total == 300
    assert reviews_total == 500
    assert events_total == 1000
