from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.product import Product
from app.schemas.common import PaginatedResponse
from app.schemas.product import ProductRead
from app.schemas.response import APIResponse
from app.utils.pagination import paginate

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[ProductRead],
    summary="Get paginated list of products with filters",
)
async def get_products(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    search: str | None = Query(
        None, description="Search by product name, brand or description"
    ),
    category_id: int | None = Query(None, description="Filter by category ID"),
    brand: str | None = Query(None, description="Filter by brand"),
    price_min: Decimal | None = Query(None, ge=0, description="Minimum price"),
    price_max: Decimal | None = Query(None, ge=0, description="Maximum price"),
    in_stock: bool | None = Query(
        None, description="Filter: true = in stock, false = out of stock"
    ),
    sort_by: str = Query(
        "created_at",
        pattern="^(price|stock|created_at)$",
        description="Sort field (price, stock, created_at)",
    ),
    sort_order: str = Query(
        "desc", pattern="^(asc|desc)$", description="Sort order (asc, desc)"
    ),
    db: AsyncSession = Depends(get_db),
) -> Any:
    # Filter out soft-deleted products
    query = select(Product).where(Product.is_deleted == False)

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                Product.name.ilike(search_filter),
                Product.brand.ilike(search_filter),
                Product.description.ilike(search_filter),
            )
        )

    if category_id is not None:
        query = query.where(Product.category_id == category_id)

    if brand:
        query = query.where(Product.brand == brand)

    if price_min is not None:
        query = query.where(Product.price >= price_min)

    if price_max is not None:
        query = query.where(Product.price <= price_max)

    if in_stock is not None:
        if in_stock:
            query = query.where(Product.stock > 0)
        else:
            query = query.where(Product.stock == 0)

    # Determine sorting column
    sort_col: Any = Product.created_at
    if sort_by == "price":
        sort_col = Product.price
    elif sort_by == "stock":
        sort_col = Product.stock

    if sort_order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    paginated_data = await paginate(db, query, page, size)
    return paginated_data


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Get a single product by ID",
)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve a single product by its ID, excluding soft-deleted products."""
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.is_deleted == False)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    return product


@router.get(
    "/{product_id}/similar",
    response_model=APIResponse[list[ProductRead]],
    summary="Get similar products",
)
async def get_similar_products(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve similar products using content-based category, brand, and price comparison."""
    # Find the target product
    target_result = await db.execute(
        select(Product).where(Product.id == product_id, Product.is_deleted == False)
    )
    target_product = target_result.scalar_one_or_none()
    if not target_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    # Fetch all candidate products
    candidates_result = await db.execute(
        select(Product).where(Product.id != product_id, Product.is_deleted == False, Product.is_active == True)
    )
    candidates = candidates_result.scalars().all()

    # Calculate content similarities using SimilarityEngine
    from app.services.ml.similarity_engine import SimilarityEngine
    engine = SimilarityEngine(db)
    similar_scores = await engine.compute_content_similarity(target_product, candidates)

    # Pick top 5 similar products
    top_similar_products = [prod for prod, score in similar_scores[:5]]

    return APIResponse(
        success=True,
        message="Similar products retrieved successfully.",
        data=top_similar_products
    )
