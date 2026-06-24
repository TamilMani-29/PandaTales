"""Seed test user for development"""

import asyncio
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.user import User

settings = get_settings()


async def seed_test_user():
    """Create a test user with a known UUID for development"""
    
    # Create async engine
    engine = create_async_engine(
        str(settings.DATABASE_URL),
        echo=True,
        future=True,
    )
    
    # Create session
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    test_user_id = UUID("00000000-0000-0000-0000-000000000001")
    
    async with async_session() as session:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.id == test_user_id)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"Test user already exists: {existing_user.email}")
            return
        
        # Create test user
        test_user = User(
            id=test_user_id,
            email="test@pandatales.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7MXvL1pm",  # password: test123
            first_name="Test",
            last_name="User",
            phone="+1234567890",
            email_verified=True,
            role="user",
        )
        
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        
        print(f"✅ Test user created successfully!")
        print(f"   Email: {test_user.email}")
        print(f"   ID: {test_user.id}")
        print(f"   Password: test123")
    
    await engine.dispose()


if __name__ == "__main__":
    print("🌱 Seeding test user...")
    asyncio.run(seed_test_user())
    print("✨ Done!")
