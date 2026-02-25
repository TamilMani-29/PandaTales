"""User Service - Business Logic Layer"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BadRequestException
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service for user business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = UserRepository(db)

    async def get_user_profile(self, user_id: UUID) -> User:
        """Get user profile by ID"""
        return await self.repository.get_by_id(user_id)

    async def update_user_profile(self, user_id: UUID, user_data: UserUpdate) -> User:
        """Update user profile"""
        return await self.repository.update(user_id, user_data)

    async def update_avatar(self, user_id: UUID, avatar_url: str) -> User:
        """Update user avatar"""
        return await self.repository.update_avatar(user_id, avatar_url)

    async def delete_account(
        self, user_id: UUID, password: str, confirmation: str
    ) -> None:
        """Delete user account with confirmation"""
        # Validate confirmation text
        if confirmation != "DELETE MY ACCOUNT":
            raise BadRequestException(
                message="Invalid confirmation text",
                error_code="INVALID_CONFIRMATION",
            )

        # TODO: Verify password (requires auth integration)
        # For now, we just do the soft delete
        await self.repository.delete(user_id)

    async def verify_email(self, user_id: UUID) -> User:
        """Mark user email as verified"""
        return await self.repository.verify_email(user_id)

    async def verify_phone(self, user_id: UUID) -> User:
        """Mark user phone as verified"""
        return await self.repository.verify_phone(user_id)
