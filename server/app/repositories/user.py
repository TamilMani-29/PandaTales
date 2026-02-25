"""User Repository - Data Access Layer"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundException
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    """Repository for user data access"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID, include_inactive: bool = False) -> User:
        """Get user by ID"""
        query = select(User).where(User.id == user_id)

        if not include_inactive:
            query = query.where(User.is_active == True)

        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException(
                message="User not found",
                error_code="USER_NOT_FOUND",
                details={"user_id": str(user_id)},
            )

        return user

    async def get_by_email(self, email: str, include_inactive: bool = False) -> User | None:
        """Get user by email"""
        query = select(User).where(User.email == email)

        if not include_inactive:
            query = query.where(User.is_active == True)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_oauth(
        self, provider: str, provider_id: str, include_inactive: bool = False
    ) -> User | None:
        """Get user by OAuth provider and ID"""
        query = select(User).where(
            User.oauth_provider == provider,
            User.oauth_provider_id == provider_id,
        )

        if not include_inactive:
            query = query.where(User.is_active == True)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, user_data: UserCreate, password_hash: str) -> User:
        """Create a new user"""
        user = User(
            email=user_data.email,
            password_hash=password_hash,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: UUID, user_data: UserUpdate) -> User:
        """Update user profile"""
        user = await self.get_by_id(user_id, include_inactive=True)

        # Update only provided fields
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_avatar(self, user_id: UUID, avatar_url: str) -> User:
        """Update user avatar URL"""
        user = await self.get_by_id(user_id)
        user.avatar_url = avatar_url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user_id: UUID) -> None:
        """Soft delete user account"""
        user = await self.get_by_id(user_id, include_inactive=True)
        user.is_active = False
        await self.db.commit()

    async def verify_email(self, user_id: UUID) -> User:
        """Mark email as verified"""
        user = await self.get_by_id(user_id)
        user.email_verified = True
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def verify_phone(self, user_id: UUID) -> User:
        """Mark phone as verified"""
        user = await self.get_by_id(user_id)
        user.phone_verified = True
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_last_login(self, user_id: UUID) -> None:
        """Update last login timestamp"""
        from datetime import datetime

        user = await self.get_by_id(user_id)
        user.last_login_at = datetime.now()
        await self.db.commit()
