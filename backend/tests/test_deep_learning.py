import os
import uuid
from decimal import Decimal

import pytest
import torch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models import Category, Event, Order, OrderItem, Product, User
from app.services.deep_learning.dataset import (
    build_interaction_matrix,
    get_ncf_dataloaders,
)
from app.services.deep_learning.model import NCFModel
from app.services.deep_learning.predict import NCFPredictor
from app.services.deep_learning.train import MODEL_DIR, train_ncf_model
from app.services.ml.scheduler import run_ncf_evaluation_pipeline

# To keep compat with existing test setup, we will use standard pytest marks.


@pytest.mark.anyio
@pytest.mark.usefixtures("init_db")
async def test_dataset_generation_and_loading(db_session: AsyncSession) -> None:
    """Verify that interaction matrices are properly generated and loaders split correctly."""
    # Seed active user, category and product
    user = User(
        full_name="Deep Learner",
        email="ncf_test@example.com",
        password_hash="hash",
        role="customer",
        is_deleted=False,
        is_active=True,
    )
    db_session.add(user)

    cat = Category(name="Gear", slug="gear")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(cat)

    prod = Product(
        category_id=cat.id,
        name="Climbing Chalk",
        slug="chalk",
        brand="BlackDiamond",
        price=Decimal("15.00"),
        stock=50,
        is_deleted=False,
        is_active=True,
    )
    db_session.add(prod)
    await db_session.commit()
    await db_session.refresh(prod)

    # Seed events for interactions matrix weights computation
    event = Event(
        user_id=user.id,
        product_id=prod.id,
        event_type="view_item",
        session_id=uuid.uuid4(),
    )
    db_session.add(event)
    await db_session.commit()

    # Generate interaction matrix
    data = await build_interaction_matrix(db_session)
    assert len(data) >= 1
    assert data[0]["user_id"] == user.id
    assert data[0]["product_id"] == prod.id
    assert data[0]["weight"] == 1.0  # View weight

    # Get dataloaders
    train_loader, _test_loader, metadata = await get_ncf_dataloaders(
        db_session, batch_size=2
    )
    assert metadata["num_users"] >= 1
    assert metadata["num_products"] >= 1
    assert len(train_loader) > 0


@pytest.mark.anyio
async def test_ncf_model_forward_pass() -> None:
    """Verify forward prop math dimension checks."""
    model = NCFModel(num_users=10, num_products=5, embedding_dim=8, layers=[16, 8])
    u_idx = torch.tensor([0, 2, 4], dtype=torch.long)
    p_idx = torch.tensor([1, 3, 0], dtype=torch.long)

    scores = model(u_idx, p_idx)
    assert scores.shape == (3,)
    assert torch.all(scores >= 0.0)
    assert torch.all(scores <= 1.0)


@pytest.mark.anyio
@pytest.mark.usefixtures("init_db")
async def test_ncf_training_and_saving(db_session: AsyncSession) -> None:
    """Executes a short training cycle to verify checkpoints saving."""
    # Seed interactions
    user = User(
        full_name="Deep Trainer",
        email="ncf_train@example.com",
        password_hash="hash",
        role="customer",
        is_deleted=False,
        is_active=True,
    )
    db_session.add(user)

    cat = Category(name="Gear", slug="gear")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(cat)

    prod = Product(
        category_id=cat.id,
        name="Climbing Chalk Bag",
        slug="chalk-bag",
        brand="BlackDiamond",
        price=Decimal("25.00"),
        stock=20,
        is_deleted=False,
        is_active=True,
    )
    db_session.add(prod)
    await db_session.commit()
    await db_session.refresh(prod)

    # Seed order interaction (weight 5)
    order = Order(
        user_id=user.id,
        status="completed",
        subtotal=Decimal("25.00"),
        tax=Decimal("2.00"),
        discount=Decimal("0.00"),
        total=Decimal("27.00"),
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    item = OrderItem(
        order_id=order.id,
        product_id=prod.id,
        quantity=1,
        unit_price=Decimal("25.00"),
        subtotal=Decimal("25.00"),
    )
    db_session.add(item)
    await db_session.commit()

    # Train model (2 epochs only for test speed)
    metadata_payload = await train_ncf_model(
        db_session, epochs=2, batch_size=2, embedding_dim=4, layers=[8, 4]
    )

    assert "version" in metadata_payload
    assert os.path.exists(os.path.join(MODEL_DIR, "latest.pt"))
    assert os.path.exists(os.path.join(MODEL_DIR, "model_metadata.json"))

    # Verify model predictor loads weights successfully
    predictor = NCFPredictor()
    assert predictor.is_loaded is True

    # Check score prediction
    score = await predictor.predict_score(user.id, prod.id)
    assert 0.0 <= score <= 1.0

    # Check recommendations list
    recs = await predictor.recommend_for_user(user.id, db_session)
    assert len(recs) >= 0

    # Run scheduler evaluation pipeline
    await run_ncf_evaluation_pipeline(db_session)
    assert os.path.exists(os.path.join(MODEL_DIR, "evaluation_metrics.json"))


@pytest.mark.anyio
@pytest.mark.usefixtures("init_db")
async def test_deep_recommendations_endpoints(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Verifies that the /deep, /deep/similar, and /deep/compare endpoints respond correctly."""
    user = User(
        full_name="Deep REST user",
        email="ncf_api@example.com",
        password_hash="hash",
        role="customer",
        is_deleted=False,
        is_active=True,
    )
    db_session.add(user)

    cat = Category(name="Gear", slug="gear")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(cat)

    prod = Product(
        category_id=cat.id,
        name="Climbing Shoes",
        slug="shoes",
        brand="LaSportiva",
        price=Decimal("175.00"),
        stock=5,
        is_deleted=False,
        is_active=True,
    )
    db_session.add(prod)
    await db_session.commit()
    await db_session.refresh(prod)

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test GET /deep
    res = await client.get("/api/v1/recommendations/deep", headers=headers)
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 2. Test GET /deep/similar/{product_id}
    res = await client.get(
        f"/api/v1/recommendations/deep/similar/{prod.id}", headers=headers
    )
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 3. Test GET /deep/compare
    res = await client.get("/api/v1/recommendations/deep/compare", headers=headers)
    assert res.status_code == 200
    assert "hybrid" in res.json()["data"]
    assert "deep" in res.json()["data"]
