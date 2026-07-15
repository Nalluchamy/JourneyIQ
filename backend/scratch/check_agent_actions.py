import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.agent_action import AgentAction

async def main():
    # Database URL with asyncpg
    url = "postgresql+asyncpg://postgres.qhkbuszwzxejyataswph:bWDsNo41jfgMIBke@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
    engine = create_async_engine(url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        stmt = select(AgentAction).order_by(AgentAction.id.desc()).limit(10)
        res = await db.execute(stmt)
        actions = res.scalars().all()
        
        print("=== LAST 10 AGENT ACTIONS ===")
        for a in actions:
            print(f"ID: {a.id} | Title: {a.title} | Status: {a.status}")
            if a.error_message:
                print(f"   ↳ Error: {a.error_message}")
            if a.execution_result:
                print(f"   ↳ Result: {a.execution_result}")
            print("-" * 50)

asyncio.run(main())
