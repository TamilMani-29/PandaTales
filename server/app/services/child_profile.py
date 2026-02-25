"""Child Profile Service - Business Logic Layer"""

from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.child_profile import ChildProfile
from app.repositories.child_profile import ChildProfileRepository
from app.schemas.user import ChildProfileCreate, ChildProfileUpdate


class ChildProfileService:
    """Service for child profile business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ChildProfileRepository(db)

    async def get_child_profile(self, child_id: UUID, user_id: UUID) -> ChildProfile:
        """Get child profile by ID"""
        return await self.repository.get_by_id(child_id, user_id=user_id)

    async def list_children(self, user_id: UUID) -> Sequence[ChildProfile]:
        """List all child profiles for a user"""
        return await self.repository.get_all_by_user(user_id)

    async def create_child_profile(
        self, user_id: UUID, child_data: ChildProfileCreate
    ) -> ChildProfile:
        """Create a new child profile"""
        return await self.repository.create(user_id, child_data)

    async def update_child_profile(
        self, child_id: UUID, user_id: UUID, child_data: ChildProfileUpdate
    ) -> ChildProfile:
        """Update a child profile"""
        return await self.repository.update(child_id, user_id, child_data)

    async def update_photo(
        self, child_id: UUID, user_id: UUID, photo_url: str
    ) -> ChildProfile:
        """Update child profile photo"""
        return await self.repository.update_photo(child_id, user_id, photo_url)

    async def delete_child_profile(self, child_id: UUID, user_id: UUID) -> None:
        """Delete a child profile"""
        await self.repository.delete(child_id, user_id)
