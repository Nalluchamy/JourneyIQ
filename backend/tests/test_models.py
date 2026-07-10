import datetime
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Category,
    Event,
    Product,
    Review,
    User,
)


@pytest.mark.asyncio
async def test_user_creation_and_soft_delete(db_session: AsyncSession) -> None:
    # Test User insert
    user = User(
        full_name="John Doe",
        email="john@example.com",
        password_hash="hashed_pw_123",
        role="customer",
    )
    db_session.add(user)
    await db_session.commit()

    assert user.id is not None
    assert user.is_deleted is False
    assert user.is_active is True

    # Test soft delete
    user.is_deleted = True
    user.deleted_at = datetime.datetime.now(datetime.UTC)
    await db_session.commit()

    # Re-fetch and check status
    stmt = select(User).where(User.id == user.id)
    res = await db_session.execute(stmt)
    db_user = res.scalar()
    assert db_user is not None
    assert db_user.is_deleted is True
    assert db_user.deleted_at is not None


@pytest.mark.asyncio
async def test_category_and_product_relationship(db_session: AsyncSession) -> None:
    # Create Category
    cat = Category(name="Electronics", slug="electronics", description="Gadgets")
    db_session.add(cat)
    await db_session.commit()

    # Create Product
    prod = Product(
        category_id=cat.id,
        name="Smartphone",
        slug="smartphone",
        description="Premium smartphone",
        price=Decimal("499.99"),
        stock=50,
    )
    db_session.add(prod)
    await db_session.commit()

    # Verify relationships
    assert prod.id is not None
    assert prod.category.name == "Electronics"

    # Re-fetch category and check associated products
    res = await db_session.execute(
        select(Category)
        .options(selectinload(Category.products))
        .where(Category.id == cat.id)
    )
    db_cat = res.scalar()
    assert db_cat is not None
    assert len(db_cat.products) == 1
    assert db_cat.products[0].name == "Smartphone"


@pytest.mark.asyncio
async def test_review_rating_check_constraint(db_session: AsyncSession) -> None:
    user = User(full_name="Alice", email="alice@example.com", password_hash="pw")
    cat = Category(name="Fashion", slug="fashion")
    db_session.add_all([user, cat])
    await db_session.commit()

    prod = Product(
        category_id=cat.id,
        name="Shirt",
        slug="shirt",
        price=Decimal("19.99"),
        stock=10,
    )
    db_session.add(prod)
    await db_session.commit()

    # Rating > 5 check constraint should fail
    invalid_review = Review(
        user_id=user.id,
        product_id=prod.id,
        rating=6,  # Invalid rating (must be 1-5)
        review="Amazing!",
    )
    db_session.add(invalid_review)

    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_event_uuid_session(db_session: AsyncSession) -> None:
    session_uuid = uuid.uuid4()
    event = Event(
        session_id=session_uuid,
        event_type="page_view",
        page="/home",
        metadata_={"browser": "chrome"},
    )
    db_session.add(event)
    await db_session.commit()

    assert event.id is not None
    assert event.session_id == session_uuid
    assert event.metadata_ == {"browser": "chrome"}
