import asyncio
from app.db.session import AsyncSessionLocal
from app.models import Product, User
from sqlalchemy import select, func

async def check():
    async with AsyncSessionLocal() as db:
        prod_count = await db.scalar(select(func.count(Product.id)))
        user_count = await db.scalar(select(func.count(User.id)))
        print(f"=====================================")
        print(f"DATABASE SEED VERIFICATION")
        print(f"=====================================")
        print(f"Total Products: {prod_count}")
        print(f"Total Users   : {user_count}")
        print(f"=====================================")

asyncio.run(check())
