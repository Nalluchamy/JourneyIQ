import pytest
from fastapi import APIRouter
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin, require_customer, require_owner, require_staff
from app.core.security import create_access_token
from app.main import app
from app.models.user import User

# Add dynamic mock endpoints to the live app routing table to verify dependency injections under test requests
router = APIRouter(prefix="/test-roles", tags=["test_roles"])


@router.get("/customer", dependencies=[require_customer])
def customer_endpoint() -> dict[str, str]:
    return {"access": "granted"}


@router.get("/staff", dependencies=[require_staff])
def staff_endpoint() -> dict[str, str]:
    return {"access": "granted"}


@router.get("/owner", dependencies=[require_owner])
def owner_endpoint() -> dict[str, str]:
    return {"access": "granted"}


@router.get("/admin", dependencies=[require_admin])
def admin_endpoint() -> dict[str, str]:
    return {"access": "granted"}


app.include_router(router)


@pytest.mark.asyncio
async def test_get_users_me_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_users_me_authorized(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = User(
        email="me_authorized@example.com",
        password_hash="pw",
        full_name="Me Authorized",
        role="customer",
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Me Authorized"
    assert data["email"] == "me_authorized@example.com"


@pytest.mark.asyncio
async def test_patch_users_me(client: AsyncClient, db_session: AsyncSession) -> None:
    user = User(
        email="patch_me@example.com",
        password_hash="pw",
        full_name="Original Name",
        role="customer",
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {"full_name": "Updated Name", "phone": "+987654321"}
    response = await client.patch(
        "/api/v1/users/me", json=update_payload, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["phone"] == "+987654321"


@pytest.mark.asyncio
async def test_role_guards(client: AsyncClient, db_session: AsyncSession) -> None:
    # 1. Create a user with Customer role
    cust_user = User(
        email="guard_cust@example.com",
        password_hash="pw",
        full_name="Customer User",
        role="customer",
        is_verified=True,
    )
    # 2. Create a user with Admin role
    admin_user = User(
        email="guard_admin@example.com",
        password_hash="pw",
        full_name="Admin User",
        role="admin",
        is_verified=True,
    )
    db_session.add_all([cust_user, admin_user])
    await db_session.commit()

    cust_token = create_access_token(cust_user.id)
    admin_token = create_access_token(admin_user.id)

    # 3. Test customer accessing customer endpoint -> 200 OK
    res1 = await client.get(
        "/test-roles/customer", headers={"Authorization": f"Bearer {cust_token}"}
    )
    assert res1.status_code == 200

    # 4. Test customer accessing admin endpoint -> 403 Forbidden
    res2 = await client.get(
        "/test-roles/admin", headers={"Authorization": f"Bearer {cust_token}"}
    )
    assert res2.status_code == 403

    # 5. Test admin accessing admin endpoint -> 200 OK
    res3 = await client.get(
        "/test-roles/admin", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res3.status_code == 200
