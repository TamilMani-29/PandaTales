"""Child Profile Repository - Data Access Layer"""

from typing import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ForbiddenException, NotFoundException
from app.models.child_profile import ChildProfile
from app.schemas.user import ChildProfileCreate, ChildProfileUpdate


class ChildProfileRepository:
    """Repository for child profile data access"""

    MAX_CHILDREN_PER_USER = 10

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self, child_id: UUID, user_id: UUID | None = None, include_inactive: bool = False
    ) -> ChildProfile:
        """Get child profile by ID"""
        query = select(ChildProfile).where(ChildProfile.id == child_id)

        if user_id:
            query = query.where(ChildProfile.user_id == user_id)

        if not include_inactive:
            query = query.where(ChildProfile.is_active == True)

        result = await self.db.execute(query)
        child = result.scalar_one_or_none()

        if not child:
            raise NotFoundException(
                message="Child profile not found",
                error_code="CHILD_NOT_FOUND",
                details={"child_id": str(child_id)},
            )

        # Check ownership if user_id provided
        if user_id and child.user_id != user_id:
            raise ForbiddenException(
                message="Not authorized to access this child profile",
                error_code="UNAUTHORIZED_ACCESS",
            )

        return child

    async def get_all_by_user(
        self, user_id: UUID, include_inactive: bool = False
    ) -> Sequence[ChildProfile]:
        """Get all child profiles for a user"""
        query = select(ChildProfile).where(ChildProfile.user_id == user_id)

        if not include_inactive:
            query = query.where(ChildProfile.is_active == True)

        query = query.order_by(ChildProfile.created_at.desc())

        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_by_user(self, user_id: UUID, include_inactive: bool = False) -> int:
        """Count child profiles for a user"""
        query = select(func.count(ChildProfile.id)).where(ChildProfile.user_id == user_id)

        if not include_inactive:
            query = query.where(ChildProfile.is_active == True)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def create(self, user_id: UUID, child_data: ChildProfileCreate) -> ChildProfile:
        """Create a new child profile"""
        # Check maximum limit
        count = await self.count_by_user(user_id, include_inactive=False)
        if count >= self.MAX_CHILDREN_PER_USER:
            raise ForbiddenException(
                message=f"Maximum child profiles limit reached ({self.MAX_CHILDREN_PER_USER})",
                error_code="MAX_CHILDREN_LIMIT",
                details={"limit": self.MAX_CHILDREN_PER_USER},
            )

        child = ChildProfile(
            user_id=user_id,
            **child_data.model_dump(),
        )
        self.db.add(child)
        await self.db.commit()
        await self.db.refresh(child)
        return child

    async def update(
        self, child_id: UUID, user_id: UUID, child_data: ChildProfileUpdate
    ) -> ChildProfile:
        """Update a child profile"""
        child = await self.get_by_id(child_id, user_id=user_id, include_inactive=True)

        # Update only provided fields
        update_data = child_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(child, field, value)

        await self.db.commit()
        await self.db.refresh(child)
        return child

    async def update_photo(self, child_id: UUID, user_id: UUID, photo_url: str) -> ChildProfile:
        """Update child profile photo URL"""
        child = await self.get_by_id(child_id, user_id=user_id)
        child.photo_url = photo_url
        await self.db.commit()
        await self.db.refresh(child)
        return child

    async def delete(self, child_id: UUID, user_id: UUID) -> None:
        """Soft delete a child profile"""
        child = await self.get_by_id(child_id, user_id=user_id, include_inactive=True)
        child.is_active = False
        await self.db.commit()

    async def increment_books_count(self, child_id: UUID) -> None:
        """Increment books created count"""
        child = await self.get_by_id(child_id, include_inactive=False)
        child.books_created_count += 1
        await self.db.commit()
