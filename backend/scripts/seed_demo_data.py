"""Seed script: creates demo org, users, and connection for testing."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_factory
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.user import User


async def seed():
    async with async_session_factory() as session:
        # Create organization
        org = Organization(
            name="NovaTech Manufacturing GmbH",
            slug="novatech",
            plan="pro",
            max_connections=20,
            max_users=50,
        )
        session.add(org)
        await session.flush()

        # Create users
        users = [
            User(
                org_id=org.id,
                email="admin@novatech.com",
                password_hash=hash_password("admin123"),
                full_name="Alex Admin",
                role="admin",
            ),
            User(
                org_id=org.id,
                email="analyst@novatech.com",
                password_hash=hash_password("analyst123"),
                full_name="Ana Analyst",
                role="analyst",
            ),
            User(
                org_id=org.id,
                email="viewer@novatech.com",
                password_hash=hash_password("viewer123"),
                full_name="Val Viewer",
                role="viewer",
            ),
        ]
        for u in users:
            session.add(u)

        await session.commit()
        print("Seed data created successfully!")
        print(f"  Organization: {org.name} (slug: {org.slug})")
        print(f"  Users: admin@novatech.com / analyst@novatech.com / viewer@novatech.com")
        print(f"  Passwords: admin123 / analyst123 / viewer123")


if __name__ == "__main__":
    asyncio.run(seed())
