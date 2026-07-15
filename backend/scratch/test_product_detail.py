import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy import select
from app.models.product import Product
from app.schemas.product import ProductRead

async def test():
    # Connect to local SQLite DB
    engine = create_async_engine("sqlite+aiosqlite:///journeyiq.db")
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        # Fetch any product in the DB to see if serialization works
        result = await db.execute(
            select(Product)
            .options(selectinload(Product.images), selectinload(Product.variants))
            .limit(1)
        )
        product = result.scalar_one_or_none()
        if not product:
            print("No products found in local SQLite database!")
            return
        
        print(f"Product ID: {product.id}")
        print(f"Product Name: {product.name}")
        print("Attempting validation via ProductRead...")
        try:
            pydantic_product = ProductRead.model_validate(product)
            print("✓ Validation successful!")
            print(f"Serialized keys: {list(pydantic_product.model_dump().keys())}")
        except Exception as e:
            print("✗ Validation failed!")
            import traceback
            traceback.print_exc()

asyncio.run(test())
