from fastapi import APIRouter

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
)

api_router = APIRouter()

# Register endpoints
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(wishlist.router, prefix="/wishlist", tags=["wishlist"])
api_router.include_router(cart.router, prefix="/cart", tags=["cart"])
api_router.include_router(reviews.router, tags=["reviews"])
api_router.include_router(addresses.router, prefix="/addresses", tags=["addresses"])
api_router.include_router(checkout.router, tags=["checkout"])
api_router.include_router(coupons.router, prefix="/coupons", tags=["coupons"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
