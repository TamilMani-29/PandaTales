"""User Service - Business Logic Layer"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BadRequestException
from app.common.logging import get_logger
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate

logger = get_logger(__name__)


class UserService:
    """Service for user business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = UserRepository(db)

    async def get_user_profile(self, user_id: UUID) -> User:
        """Get user profile by ID"""
        logger.info("fetching_user_profile", user_id=str(user_id))
        return await self.repository.get_by_id(user_id)

    async def update_user_profile(self, user_id: UUID, user_data: UserUpdate) -> User:
        """Update user profile"""
        logger.info("updating_user_profile", user_id=str(user_id))
        user = await self.repository.update(user_id, user_data)
        logger.info("user_profile_updated", user_id=str(user.id), email=user.email)
        return user

    async def update_avatar(self, user_id: UUID, avatar_url: str) -> User:
        """Update user avatar"""
        logger.info("updating_user_avatar", user_id=str(user_id))
        user = await self.repository.update_avatar(user_id, avatar_url)
        logger.info("user_avatar_updated", user_id=str(user.id))
        return user

    async def delete_account(
        self, user_id: UUID, password: str, confirmation: str
    ) -> None:
        """Delete user account with confirmation"""
        logger.warning("account_deletion_requested", user_id=str(user_id))
        
        # Validate confirmation text
        if confirmation != "DELETE MY ACCOUNT":
            logger.warning("account_deletion_failed_invalid_confirmation", user_id=str(user_id))
            raise BadRequestException(
                message="Invalid confirmation text",
                error_code="INVALID_CONFIRMATION",
            )

        # TODO: Verify password (requires auth integration)
        # For now, we just do the soft delete
        await self.repository.delete(user_id)
        logger.warning("account_deleted", user_id=str(user_id))

    async def verify_email(self, user_id: UUID) -> User:
        """Mark user email as verified"""
        logger.info("verifying_user_email", user_id=str(user_id))
        user = await self.repository.verify_email(user_id)
        logger.info("user_email_verified", user_id=str(user.id), email=user.email)
        return user

    async def verify_phone(self, user_id: UUID) -> User:
        """Mark user phone as verified"""
        logger.info("verifying_user_phone", user_id=str(user_id))
        user = await self.repository.verify_phone(user_id)
        logger.info("user_phone_verified", user_id=str(user.id), phone=user.phone)
        return user
