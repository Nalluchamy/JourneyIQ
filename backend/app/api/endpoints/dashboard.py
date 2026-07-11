import csv
import datetime
import io
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.order import Order
from app.models.product import Product
from app.schemas.response import APIResponse
from app.services.analytics.customer_intelligence import CustomerIntelligenceService
from app.services.analytics.funnel import JourneyFunnelService
from app.services.analytics.sales_product import SalesProductAnalyticsService
from app.services.analytics.insights import AIInsightsService

router = APIRouter()

from app.core.cache import cache


def get_cached_data(key: str) -> Optional[Any]:
    """Retrieve non-expired data from application cache."""
    return cache.get(key)


def set_cached_data(key: str, data: Any) -> None:
    """Store data in application cache."""
    cache.set(key, data, ttl_seconds=900)


def clear_analytics_cache() -> None:
    """Clear all dashboard cache records."""
    cache.clear()


def check_owner_access(current_user: User) -> None:
    """Verify requesting user is an administrator/owner."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin access required."
        )


@router.get("/overview", response_model=APIResponse[dict[str, Any]], summary="Get Overview Metrics")
async def get_overview(
    date_range: str = Query("last_30_days", description="Date range: today, yesterday, last_7_days, last_30_days, this_month, custom"),
    start_date: Optional[str] = Query(None, description="Start date format YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date format YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve dashboard main overview KPI cards, date comparative deltas, and inventory alerts."""
    check_owner_access(current_user)

    cache_key = f"overview_{date_range}_{start_date}_{end_date}"
    cached = get_cached_data(cache_key)
    if cached is not None:
        return APIResponse(success=True, message="Cached metrics loaded.", data=cached)

    start_dt, end_dt = None, None
    if start_date and end_date:
        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    sales_service = SalesProductAnalyticsService(db)
    sales = await sales_service.get_sales_analytics(date_range, start_dt, end_dt)
    products = await sales_service.get_product_analytics()
    intel_service = CustomerIntelligenceService(db)
    customers = await intel_service.calculate_rfm_and_segmentation()

    # Calculate live metrics
    active_sessions = len(set([c["user_id"] for c in customers if c["recency_days"] <= 1])) # session proxy (active in 1 day)

    # Compile result payload
    payload = {
        "summary": sales["summary"],
        "active_sessions": active_sessions,
        "inventory_alerts": products["inventory_alerts"][:5],
        "timeline": sales["timeline"]
    }

    set_cached_data(cache_key, payload)
    return APIResponse(success=True, message="Overview metrics calculated.", data=payload)


@router.get("/customers", response_model=APIResponse[list[dict[str, Any]]], summary="Get Customer Intelligence")
async def get_customers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve detailed customers intelligence containing segments, churn probabilities, and CLV metrics."""
    check_owner_access(current_user)

    cache_key = "customers_intel"
    cached = get_cached_data(cache_key)
    if cached is not None:
        return APIResponse(success=True, message="Cached customer intelligence loaded.", data=cached)

    service = CustomerIntelligenceService(db)
    data = await service.calculate_rfm_and_segmentation()

    set_cached_data(cache_key, data)
    return APIResponse(success=True, message="Customer intelligence calculations generated.", data=data)


@router.get("/products", response_model=APIResponse[dict[str, Any]], summary="Get Product Analytics")
async def get_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve product velocity lists (top/lowest sellers, fast-moving, slow-moving items) and stockout alerts."""
    check_owner_access(current_user)

    cache_key = "product_analytics"
    cached = get_cached_data(cache_key)
    if cached is not None:
        return APIResponse(success=True, message="Cached product velocity logs loaded.", data=cached)

    service = SalesProductAnalyticsService(db)
    data = await service.get_product_analytics()

    set_cached_data(cache_key, data)
    return APIResponse(success=True, message="Product velocity logs calculated.", data=data)


@router.get("/orders", response_model=APIResponse[dict[str, Any]], summary="Get Orders Analytics")
async def get_orders(
    date_range: str = Query("last_30_days", description="Date range: today, yesterday, last_7_days, last_30_days, this_month, custom"),
    start_date: Optional[str] = Query(None, description="Start date format YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date format YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve order summaries, status distribution graphs, coupon usage metrics, and recent order items list."""
    check_owner_access(current_user)

    cache_key = f"orders_{date_range}_{start_date}_{end_date}"
    cached = get_cached_data(cache_key)
    if cached is not None:
        return APIResponse(success=True, message="Cached order logs loaded.", data=cached)

    start_dt, end_dt = None, None
    if start_date and end_date:
        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    sales_service = SalesProductAnalyticsService(db)
    sales = await sales_service.get_sales_analytics(date_range, start_dt, end_dt)

    orders_stmt = select(Order).options(selectinload(Order.user)).order_by(Order.created_at.desc()).limit(20)
    recent_orders = (await db.execute(orders_stmt)).scalars().all()

    recent_orders_list = [
        {
            "id": o.id,
            "invoice_number": o.invoice_number or f"INV-{o.id}",
            "customer_name": o.user.full_name if o.user else "Guest",
            "total": float(o.total),
            "status": o.status,
            "created_at": o.created_at
        }
        for o in recent_orders
    ]

    payload = {
        "summary": sales["summary"],
        "recent_orders": recent_orders_list
    }

    set_cached_data(cache_key, payload)
    return APIResponse(success=True, message="Order analytics summaries compiled.", data=payload)


@router.get("/analytics", response_model=APIResponse[dict[str, Any]], summary="Get Visualization Graphs")
async def get_analytics_graphs(
    date_range: str = Query("last_30_days", description="Date range: today, yesterday, last_7_days, last_30_days, this_month, custom"),
    start_date: Optional[str] = Query(None, description="Start date format YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date format YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve chart records containing revenue area data, category split counts, and transaction completion metrics."""
    check_owner_access(current_user)

    cache_key = f"analytics_graphs_{date_range}_{start_date}_{end_date}"
    cached = get_cached_data(cache_key)
    if cached is not None:
        return APIResponse(success=True, message="Cached graph metrics loaded.", data=cached)

    start_dt, end_dt = None, None
    if start_date and end_date:
        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    sales_service = SalesProductAnalyticsService(db)
    sales = await sales_service.get_sales_analytics(date_range, start_dt, end_dt)

    funnel_service = JourneyFunnelService(db)
    funnel = await funnel_service.get_conversion_funnel()

    payload = {
        "sales_timeline": sales["timeline"],
        "funnel": funnel
    }

    set_cached_data(cache_key, payload)
    return APIResponse(success=True, message="Visualization graph metrics generated.", data=payload)


@router.get("/insights", response_model=APIResponse[list[dict[str, Any]]], summary="Get AI Business Insights")
async def get_insights(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve natural-language AI business insights categorized by Priority levels (High/Medium/Low) and Action recommendations."""
    check_owner_access(current_user)

    cache_key = "ai_insights"
    cached = get_cached_data(cache_key)
    if cached is not None:
        return APIResponse(success=True, message="Cached insights loaded.", data=cached)

    service = AIInsightsService(db)
    data = await service.generate_business_insights()

    set_cached_data(cache_key, data)
    return APIResponse(success=True, message="AI Insights compiled successfully.", data=data)


@router.get("/funnel", response_model=APIResponse[dict[str, Any]], summary="Get Journey Funnel")
async def get_funnel(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve visitors conversion funnel metrics."""
    check_owner_access(current_user)
    service = JourneyFunnelService(db)
    data = await service.get_conversion_funnel()
    return APIResponse(success=True, message="Funnel data retrieved.", data=data)


@router.get("/churn", response_model=APIResponse[list[dict[str, Any]]], summary="Get Churn Analysis")
async def get_churn_analysis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve churn levels and risk indicators."""
    check_owner_access(current_user)
    service = CustomerIntelligenceService(db)
    data = await service.calculate_rfm_and_segmentation()
    churn_list = [{"user_id": c["user_id"], "customer_name": c["customer_name"], "risk_level": c["churn"]["risk_level"], "explanation": c["churn"]["explanation"]} for c in data]
    return APIResponse(success=True, message="Churn analysis retrieved.", data=churn_list)


@router.get("/clv", response_model=APIResponse[list[dict[str, Any]]], summary="Get Customer Lifetime Value")
async def get_clv_analysis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve CLV projections."""
    check_owner_access(current_user)
    service = CustomerIntelligenceService(db)
    data = await service.calculate_rfm_and_segmentation()
    clv_list = [{"user_id": c["user_id"], "customer_name": c["customer_name"], "expected_value": c["clv"]["expected_value"]} for c in data]
    return APIResponse(success=True, message="CLV analysis retrieved.", data=clv_list)


@router.get("/rfm", response_model=APIResponse[list[dict[str, Any]]], summary="Get RFM Scores")
async def get_rfm_scores(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve RFM labels and segments."""
    check_owner_access(current_user)
    service = CustomerIntelligenceService(db)
    data = await service.calculate_rfm_and_segmentation()
    rfm_list = [{"user_id": c["user_id"], "customer_name": c["customer_name"], "rfm": c["rfm"], "segment": c["segment"]} for c in data]
    return APIResponse(success=True, message="RFM analysis retrieved.", data=rfm_list)


@router.post("/refresh", response_model=APIResponse[dict[str, Any]], summary="Regenerate Analytics Cache")
async def refresh_analytics(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Clears all cached summaries, forcing database recalculations on the next load requests."""
    check_owner_access(current_user)
    clear_analytics_cache()
    return APIResponse(success=True, message="Dashboard analytics cache cleared successfully. Recalculation scheduled.", data={})


@router.get("/export", summary="Export CSV Report")
async def export_report(
    type: str = Query("orders", description="Export type: orders, customers, products, revenue"),
    date_range: str = Query("last_30_days", description="Date range: today, yesterday, last_7_days, last_30_days, this_month, custom"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Generate a downloadable CSV report file for analytics data."""
    check_owner_access(current_user)

    output = io.StringIO()
    writer = csv.writer(output)

    if type == "orders":
        # Export orders
        writer.writerow(["Order ID", "Invoice Number", "User ID", "Status", "Subtotal", "Total", "Created At"])
        orders_stmt = select(Order).order_by(Order.created_at.desc())
        orders = (await db.execute(orders_stmt)).scalars().all()
        for o in orders:
            writer.writerow([o.id, o.invoice_number or f"INV-{o.id}", o.user_id, o.status, o.subtotal, o.total, o.created_at.strftime("%Y-%m-%d %H:%M:%S")])

    elif type == "customers":
        # Export customer intelligence metrics
        writer.writerow(["User ID", "Customer Name", "Email", "Recency (Days)", "Total Orders", "Total Spend ($)", "Segment", "Churn Risk", "Expected CLV ($)"])
        service = CustomerIntelligenceService(db)
        data = await service.calculate_rfm_and_segmentation()
        for c in data:
            writer.writerow([c["user_id"], c["customer_name"], c["email"], c["recency_days"], c["order_count"], c["total_spend"], c["segment"], c["churn"]["risk_level"], c["clv"]["expected_value"]])

    elif type == "products":
        # Export product velocity metrics
        writer.writerow(["Product ID", "Product Name", "Brand", "Current Stock", "Price ($)", "Total Sales Count", "Average Rating", "Recent Views"])
        service = SalesProductAnalyticsService(db)
        data = await service.get_product_analytics()
        # Combine lists
        all_prods = data["top_selling"] + data["lowest_selling"]
        seen_pids = set()
        for p in all_prods:
            if p["product_id"] not in seen_pids:
                seen_pids.add(p["product_id"])
                writer.writerow([p["product_id"], p["name"], p["brand"], p["stock"], p["price"], p["sales"], p["rating"], p["views"]])

    elif type == "revenue":
        # Export revenue timelines
        writer.writerow(["Date", "Revenue ($)", "Order Count"])
        service = SalesProductAnalyticsService(db)
        data = await service.get_sales_analytics(date_range)
        for row in data["timeline"]:
            writer.writerow([row["date"], row["revenue"], row["orders"]])

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid export type: {type}"
        )

    output.seek(0)
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=report_{type}_{date_range}.csv"
    return response
