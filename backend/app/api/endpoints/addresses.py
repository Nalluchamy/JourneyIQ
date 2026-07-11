from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.shipping_address import ShippingAddress
from app.models.user import User
from app.schemas.shipping_address import (
    ShippingAddressCreate,
    ShippingAddressRead,
    ShippingAddressUpdate,
)

router = APIRouter()


@router.get("", response_model=list[ShippingAddressRead], summary="List all shipping addresses for current user")
async def list_addresses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve all shipping addresses created by the authenticated user, ordered by default state."""
    result = await db.execute(
        select(ShippingAddress)
        .where(ShippingAddress.user_id == current_user.id)
        .order_by(ShippingAddress.is_default.desc(), ShippingAddress.id.desc())
    )
    return result.scalars().all()


@router.post("", response_model=ShippingAddressRead, status_code=status.HTTP_201_CREATED, summary="Create a new shipping address")
async def create_address(
    address_in: ShippingAddressCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create a new shipping address. If set to default, sets all other user addresses default state to False."""
    if address_in.is_default:
        await db.execute(
            update(ShippingAddress)
            .where(ShippingAddress.user_id == current_user.id)
            .values(is_default=False)
        )

    address = ShippingAddress(
        user_id=current_user.id,
        **address_in.model_dump()
    )
    db.add(address)
    await db.commit()
    await db.refresh(address)
    return address


@router.put("/{address_id}", response_model=ShippingAddressRead, summary="Update an existing shipping address")
async def update_address(
    address_id: int,
    address_in: ShippingAddressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update shipping address properties. If default, toggles off other addresses' default states."""
    result = await db.execute(
        select(ShippingAddress).where(
            ShippingAddress.id == address_id, ShippingAddress.user_id == current_user.id
        )
    )
    address = result.scalar_one_or_none()
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found."
        )

    update_data = address_in.model_dump(exclude_unset=True)
    if update_data.get("is_default"):
        await db.execute(
            update(ShippingAddress)
            .where(ShippingAddress.user_id == current_user.id)
            .values(is_default=False)
        )

    for field, value in update_data.items():
        setattr(address, field, value)

    await db.commit()
    await db.refresh(address)
    return address


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a shipping address")
async def delete_address(
    address_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a shipping address owned by the current user."""
    result = await db.execute(
        select(ShippingAddress).where(
            ShippingAddress.id == address_id, ShippingAddress.user_id == current_user.id
        )
    )
    address = result.scalar_one_or_none()
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found."
        )

    await db.delete(address)
    await db.commit()
