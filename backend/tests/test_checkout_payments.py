import datetime
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.cart_item import CartItem
from app.models.category import Category
from app.models.coupon import Coupon
from app.models.coupon_usage import CouponUsage
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment import Payment
from app.models.product import Product
from app.models.shipping_address import ShippingAddress
from app.models.user import User


@pytest.mark.asyncio
async def test_checkout_payments_e2e(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # 1. Create a customer user, category, and products
    user = User(
        email="checkout_user@example.com",
        password_hash="pw",
        full_name="Checkout User",
        role="customer",
        is_verified=True,
    )
    category = Category(name="Checkout Cat", slug="checkout-cat")
    db_session.add(category)
    await db_session.flush()

    product1 = Product(
        category_id=category.id,
        name="Nike Zoom",
        slug="nike-zoom",
        price=Decimal("100.00"),
        stock=10,
        is_active=True,
    )
    product2 = Product(
        category_id=category.id,
        name="Apple Case",
        slug="apple-case",
        price=Decimal("20.00"),
        stock=5,
        is_active=True,
    )
    db_session.add_all([user, product1, product2])
    await db_session.commit()

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}", "x-session-id": "22222222-3333-4444-5555-666666666666"}

    # 2. Test Address CRUD Endpoints
    # Create Address
    address_payload = {
        "full_name": "Checkout User",
        "phone": "+15551234",
        "address_line1": "123 Main St",
        "city": "Seattle",
        "state": "WA",
        "country": "USA",
        "postal_code": "98101",
        "is_default": True
    }
    addr_res = await client.post("/api/v1/addresses", json=address_payload, headers=headers)
    assert addr_res.status_code == 201
    address_id = addr_res.json()["id"]

    # List Addresses
    list_res = await client.get("/api/v1/addresses", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["city"] == "Seattle"

    # Update Address
    update_payload = {"city": "Tacoma"}
    update_res = await client.put(f"/api/v1/addresses/{address_id}", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["city"] == "Tacoma"

    # 3. Add products to cart
    cart_item1 = CartItem(user_id=user.id, product_id=product1.id, quantity=2)  # Price: 200.00
    cart_item2 = CartItem(user_id=user.id, product_id=product2.id, quantity=1)  # Price: 20.00
    db_session.add_all([cart_item1, cart_item2])
    await db_session.commit()

    # 4. Apply Coupon validation
    # Seed a demo coupon
    now = datetime.datetime.now(datetime.timezone.utc)
    expiry = now + datetime.timedelta(days=10)
    coupon = Coupon(
        code="SUPER20",
        description="20% off over $50",
        discount_type="percentage",
        discount_value=Decimal("20.00"),
        minimum_order=Decimal("50.00"),
        maximum_discount=Decimal("30.00"),
        start_date=now,
        expiry_date=expiry,
        is_active=True,
    )
    db_session.add(coupon)
    await db_session.commit()

    # Apply Coupon API
    coupon_payload = {"code": "SUPER20", "cart_total": 220.00}
    coupon_res = await client.post("/api/v1/checkout/apply-coupon", json=coupon_payload, headers=headers)
    assert coupon_res.status_code == 200
    coupon_data = coupon_res.json()
    assert coupon_data["is_valid"] is True
    # 220.00 * 20% = 44.00, capped at max_discount 30.00
    assert float(coupon_data["discount_amount"]) == 30.00

    # 5. Cart Summary Endpoint
    summary_res = await client.get("/api/v1/cart/summary?coupon_code=SUPER20", headers=headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert float(summary["subtotal"]) == 220.00
    # Tax: 220.00 * 8% = 17.60
    assert float(summary["tax"]) == 17.60
    assert float(summary["shipping"]) == 10.00
    assert float(summary["discount"]) == 30.00
    # Grand Total: 220.00 + 17.60 + 10.00 - 30.00 = 217.60
    assert float(summary["grand_total"]) == 217.60

    # 6. Checkout Endpoint
    checkout_payload = {
        "shipping_address_id": address_id,
        "coupon_code": "SUPER20"
    }
    checkout_res = await client.post("/api/v1/checkout", json=checkout_payload, headers=headers)
    assert checkout_res.status_code == 200
    checkout_data = checkout_res.json()
    assert "order_id" in checkout_data
    order_id = checkout_data["order_id"]
    invoice_number = checkout_data["invoice_number"]

    # Verify inventory was deducted
    # Nike Zoom: 10 - 2 = 8
    # Apple Case: 5 - 1 = 4
    await db_session.refresh(product1)
    await db_session.refresh(product2)
    assert product1.stock == 8
    assert product2.stock == 4

    # Verify cart was cleared
    cart_check = await db_session.execute(select(CartItem).where(CartItem.user_id == user.id))
    assert len(cart_check.scalars().all()) == 0

    # 7. Mock Payment Failure
    pay_fail = await client.post(f"/api/v1/payments/mock-failure/{order_id}", headers=headers)
    assert pay_fail.status_code == 200
    # Check order remains pending
    order_stmt = select(Order).where(Order.id == order_id)
    order_check = (await db_session.execute(order_stmt)).scalar_one()
    assert order_check.status == "pending"

    # Check payment transaction marked failed
    pay_stmt = select(Payment).where(Payment.order_id == order_id)
    payment_check = (await db_session.execute(pay_stmt)).scalar_one()
    assert payment_check.status == "failed"

    # 8. Mock Payment Success
    pay_success = await client.post(f"/api/v1/payments/mock-success/{order_id}", headers=headers)
    assert pay_success.status_code == 200
    # Check order moves to confirmed
    await db_session.refresh(order_check)
    assert order_check.status == "confirmed"

    # Check payment transaction marked success
    await db_session.refresh(payment_check)
    assert payment_check.status == "success"

    # 9. Invoice JSON Download Endpoint
    invoice_res = await client.get(f"/api/v1/orders/{order_id}/invoice", headers=headers)
    assert invoice_res.status_code == 200
    invoice_data = invoice_res.json()
    assert invoice_data["invoice_number"] == invoice_number
    assert len(invoice_data["items"]) == 2
    assert invoice_data["summary"]["total"] == 217.60

    # 10. Order Cancellation & Stock Restoration
    cancel_res = await client.patch(f"/api/v1/orders/{order_id}/cancel", headers=headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "cancelled"

    # Verify inventory was restored
    # Nike Zoom: 8 + 2 = 10
    # Apple Case: 4 + 1 = 5
    await db_session.refresh(product1)
    await db_session.refresh(product2)
    assert product1.stock == 10
    assert product2.stock == 5

    # 11. Delete Address Endpoint
    del_addr = await client.delete(f"/api/v1/addresses/{address_id}", headers=headers)
    assert del_addr.status_code == 204
