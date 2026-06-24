"""Child Profile Service - Business Logic Layer"""

from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.logging import get_logger
from app.models.child_profile import ChildProfile
from app.repositories.child_profile import ChildProfileRepository
from app.schemas.user import ChildProfileCreate, ChildProfileUpdate

logger = get_logger(__name__)


class ChildProfileService:
    """Service for child profile business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ChildProfileRepository(db)

    async def get_child_profile(self, child_id: UUID, user_id: UUID) -> ChildProfile:
        """Get child profile by ID"""
        logger.info("fetching_child_profile", child_id=str(child_id), user_id=str(user_id))
        return await self.repository.get_by_id(child_id, user_id=user_id)

    async def list_children(self, user_id: UUID) -> Sequence[ChildProfile]:
        """List all child profiles for a user"""
        logger.info("listing_child_profiles", user_id=str(user_id))
        children = await self.repository.get_all_by_user(user_id)
        logger.info("child_profiles_listed", user_id=str(user_id), count=len(children))
        return children

    async def create_child_profile(
        self, user_id: UUID, child_data: ChildProfileCreate
    ) -> ChildProfile:
        """Create a new child profile"""
        logger.info("creating_child_profile", user_id=str(user_id), name=child_data.name, age=child_data.age)
        child = await self.repository.create(user_id, child_data)
        logger.info("child_profile_created", child_id=str(child.id), user_id=str(user_id), name=child.name)
        return child

    async def update_child_profile(
        self, child_id: UUID, user_id: UUID, child_data: ChildProfileUpdate
    ) -> ChildProfile:
        """Update a child profile"""
        logger.info("updating_child_profile", child_id=str(child_id), user_id=str(user_id))
        child = await self.repository.update(child_id, user_id, child_data)
        logger.info("child_profile_updated", child_id=str(child.id), user_id=str(user_id))
        return child

    async def update_photo(
        self, child_id: UUID, user_id: UUID, photo_url: str
    ) -> ChildProfile:
        """Update child profile photo"""
        logger.info("updating_child_photo", child_id=str(child_id), user_id=str(user_id))
        child = await self.repository.update_photo(child_id, user_id, photo_url)
        logger.info("child_photo_updated", child_id=str(child.id), user_id=str(user_id))
        return child

    async def delete_child_profile(self, child_id: UUID, user_id: UUID) -> None:
        """Delete a child profile"""
        logger.info("deleting_child_profile", child_id=str(child_id), user_id=str(user_id))
        await self.repository.delete(child_id, user_id)
        logger.info("child_profile_deleted", child_id=str(child_id), user_id=str(user_id))
