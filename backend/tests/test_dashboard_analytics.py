import datetime
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models import Category, Product, User, Order, OrderItem, Segment
from app.services.analytics.customer_intelligence import CustomerIntelligenceService
from app.services.analytics.funnel import JourneyFunnelService
from app.services.analytics.sales_product import SalesProductAnalyticsService
from app.services.analytics.insights import AIInsightsService


@pytest.mark.asyncio
async def test_dashboard_analytics_services_and_apis(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # 1. Seed Categories & Products & Users
    category = Category(name="Verify Category", slug="verify-cat")
    db_session.add(category)
    await db_session.flush()

    prod = Product(
        category_id=category.id,
        name="Nike Running Shoes",
        slug="nike-run",
        brand="Nike",
        price=Decimal("120.00"),
        stock=4, # low stock (<= 5)
        is_active=True,
    )
    db_session.add(prod)
    await db_session.flush()

    # Create an admin user to access the owner dashboard
    admin_user = User(
        email="admin@example.com",
        password_hash="hash",
        full_name="Admin Owner",
        role="admin",
        is_verified=True,
    )
    # Create a customer user to test customer intelligence
    customer_user = User(
        email="customer@example.com",
        password_hash="hash",
        full_name="Customer User",
        role="customer",
        is_verified=True,
    )
    db_session.add_all([admin_user, customer_user])
    await db_session.commit()

    # Seed an order for the customer
    order = Order(
        user_id=customer_user.id,
        status="confirmed",
        subtotal=Decimal("120.00"),
        total=Decimal("129.60"),
        created_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=10) # 10 days ago (Recent)
    )
    db_session.add(order)
    await db_session.flush()

    order_item = OrderItem(
        order_id=order.id,
        product_id=prod.id,
        quantity=1,
        unit_price=prod.price,
        subtotal=prod.price
    )
    db_session.add(order_item)
    await db_session.commit()

    # 2. Test Customer Intelligence Service
    intel_service = CustomerIntelligenceService(db_session)
    results = await intel_service.calculate_rfm_and_segmentation()
    assert len(results) > 0
    
    cust_res = next(r for r in results if r["user_id"] == customer_user.id)
    assert cust_res["order_count"] == 1
    assert cust_res["total_spend"] == 129.60
    assert cust_res["segment"] == "New Customers"
    assert cust_res["churn"]["risk_level"] in ["Low", "Medium"]
    assert cust_res["clv"]["expected_value"] > 129.60

    # 3. Test Journey Funnel Service
    funnel_service = JourneyFunnelService(db_session)
    funnel = await funnel_service.get_conversion_funnel()
    assert "steps" in funnel
    assert "rates" in funnel

    # 4. Test Sales & Product Analytics Service
    sales_service = SalesProductAnalyticsService(db_session)
    sales = await sales_service.get_sales_analytics("last_30_days")
    assert sales["summary"]["total_revenue"] == 129.60
    assert sales["summary"]["order_count"] == 1

    products = await sales_service.get_product_analytics()
    assert len(products["inventory_alerts"]) > 0
    # The nike running shoes should trigger Low Stock alert (stock = 4)
    low_stock_alert = next(a for a in products["inventory_alerts"] if a["product_id"] == prod.id and a["alert_type"] == "Low Stock")
    assert low_stock_alert is not None
    assert " Nike Running Shoes remaining" in low_stock_alert["message"]

    # 5. Test AI Insights Service
    insights_service = AIInsightsService(db_session)
    insights = await insights_service.generate_business_insights()
    assert len(insights) > 0
    assert "priority" in insights[0]
    assert "action" in insights[0]

    # 6. Test GET REST API Endpoints
    token = create_access_token(admin_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # Overview API
    res_overview = await client.get("/api/v1/dashboard/overview?date_range=last_30_days", headers=headers)
    assert res_overview.status_code == 200
    assert "summary" in res_overview.json()["data"]
    assert "inventory_alerts" in res_overview.json()["data"]

    # Customers API
    res_cust = await client.get("/api/v1/dashboard/customers", headers=headers)
    assert res_cust.status_code == 200
    assert len(res_cust.json()["data"]) > 0

    # Products API
    res_prod = await client.get("/api/v1/dashboard/products", headers=headers)
    assert res_prod.status_code == 200
    assert "top_selling" in res_prod.json()["data"]

    # AI Insights API
    res_ins = await client.get("/api/v1/dashboard/insights", headers=headers)
    assert res_ins.status_code == 200
    assert len(res_ins.json()["data"]) > 0

    # Churn API
    res_churn = await client.get("/api/v1/dashboard/churn", headers=headers)
    assert res_churn.status_code == 200

    # Export API (CSV)
    res_export = await client.get("/api/v1/dashboard/export?type=orders&date_range=last_30_days", headers=headers)
    assert res_export.status_code == 200
    assert "text/csv" in res_export.headers["content-type"]
    assert "Order ID,Invoice Number" in res_export.text
