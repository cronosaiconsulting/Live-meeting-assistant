#!/usr/bin/env python3
"""
Database seeding script to create default users.

Run with: python infra/scripts/seed_db.py
"""

import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../..", "backend"))

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.services.auth_service import create_user
from sqlalchemy import select
from app.models.user import User


async def seed_database():
    """Seed the database with initial data."""
    print("🌱 Seeding database...")

    async with AsyncSessionLocal() as db:
        # Check if admin user exists
        result = await db.execute(
            select(User).where(User.username == settings.admin_default_username)
        )
        admin_user = result.scalar_one_or_none()

        if admin_user is None:
            # Create admin user
            admin_user = await create_user(
                db=db,
                username=settings.admin_default_username,
                email=settings.admin_default_email,
                password=settings.admin_default_password,
                full_name="Admin User",
                is_admin=True,
            )
            print(f"✅ Created admin user: {admin_user.username}")
        else:
            print(f"ℹ️  Admin user already exists: {admin_user.username}")

        # Create test users
        test_users = [
            ("john", "john@example.com", "user123", "John Doe"),
            ("jane", "jane@example.com", "user123", "Jane Smith"),
        ]

        for username, email, password, full_name in test_users:
            result = await db.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()

            if user is None:
                user = await create_user(
                    db=db,
                    username=username,
                    email=email,
                    password=password,
                    full_name=full_name,
                    is_admin=False,
                )
                print(f"✅ Created test user: {user.username}")
            else:
                print(f"ℹ️  Test user already exists: {user.username}")

    print("✨ Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_database())
