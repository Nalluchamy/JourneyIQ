import asyncio
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import select

async def create_admin():
    async with AsyncSessionLocal() as db:
        # Check if admin already exists
        result = await db.execute(select(User).where(User.email == "admin@journeyiq.in"))
        existing = result.scalar_one_or_none()

        if existing:
            # Reset password
            existing.password_hash = get_password_hash("Admin@1234")
            existing.role = "admin"
            existing.is_active = True
            await db.commit()
            print("✓ Admin password reset successfully!")
        else:
            # Create fresh admin
            admin = User(
                full_name="JourneyIQ Admin",
                email="admin@journeyiq.in",
                password_hash=get_password_hash("Admin@1234"),
                phone="9999999999",
                role="admin",
                is_active=True,
                is_deleted=False
            )
            db.add(admin)
            await db.commit()
            print("✓ Admin user created successfully!")

        print("")
        print("===========================")
        print("  Admin Login Credentials  ")
        print("===========================")
        print("  Email   : admin@journeyiq.in")
        print("  Password: Admin@1234")
        print("===========================")

asyncio.run(create_admin())
