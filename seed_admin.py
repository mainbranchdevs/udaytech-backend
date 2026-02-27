"""
Run this script to create or promote a user to admin.

Usage:
    python seed_admin.py admin@example.com

The user will be created if they don't exist, or promoted to admin if they do.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import select
from app.database import async_session
from app.models.user import User


async def seed_admin(email: str):
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            user.role = "admin"
            user.is_verified = True
            print(f"Promoted existing user '{email}' to admin.")
        else:
            user = User(email=email, name="Admin", role="admin", is_verified=True)
            db.add(user)
            print(f"Created new admin user '{email}'.")

        await db.commit()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python seed_admin.py <email>")
        sys.exit(1)
    asyncio.run(seed_admin(sys.argv[1]))
