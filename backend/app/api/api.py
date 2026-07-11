from fastapi import APIRouter, Depends

from app.core.rate_limiter import InMemoryRateLimiter
from app.api.endpoints import (
    auth,
    categories,
    events,
    health,
    orders,
    products,
    users,
    cart,
    wishlist,
    reviews,
    addresses,
    checkout,
    coupons,
    payments,
    recommendations,
    dashboard,
    system,
)

api_router = APIRouter()

# Rate limiter instances for each class
limiter_public = InMemoryRateLimiter(requests_limit=100, window_seconds=60)
limiter_recommendations = InMemoryRateLimiter(requests_limit=60, window_seconds=60)
limiter_dashboard = InMemoryRateLimiter(requests_limit=120, window_seconds=60)

# Register endpoints
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"], dependencies=[Depends(limiter_public)])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"], dependencies=[Depends(limiter_public)])
api_router.include_router(products.router, prefix="/products", tags=["products"], dependencies=[Depends(limiter_public)])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"], dependencies=[Depends(limiter_public)])
api_router.include_router(events.router, prefix="/events", tags=["events"], dependencies=[Depends(limiter_public)])
api_router.include_router(wishlist.router, prefix="/wishlist", tags=["wishlist"], dependencies=[Depends(limiter_public)])
api_router.include_router(cart.router, prefix="/cart", tags=["cart"], dependencies=[Depends(limiter_public)])
api_router.include_router(reviews.router, tags=["reviews"], dependencies=[Depends(limiter_public)])
api_router.include_router(addresses.router, prefix="/addresses", tags=["addresses"], dependencies=[Depends(limiter_public)])
api_router.include_router(checkout.router, tags=["checkout"], dependencies=[Depends(limiter_public)])
api_router.include_router(coupons.router, prefix="/coupons", tags=["coupons"], dependencies=[Depends(limiter_public)])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"], dependencies=[Depends(limiter_public)])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"], dependencies=[Depends(limiter_recommendations)])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(limiter_dashboard)])
api_router.include_router(system.router, prefix="/system", tags=["system"])
