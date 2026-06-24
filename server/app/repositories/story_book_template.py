"""Story Book Template Repository - Data Access Layer"""

from typing import Sequence
from uuid import UUID

from sqlalchemy import Select, and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundException
from app.models.story_book_template import StoryBookTemplate
from app.schemas.story_book_template import (
    StoryBookTemplateCreate,
    StoryBookTemplateFilters,
    StoryBookTemplateUpdate,
)


class StoryBookTemplateRepository:
    """Repository for story book template data access"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self, template_id: UUID, include_inactive: bool = False
    ) -> StoryBookTemplate:
        """Get template by ID"""
        query = select(StoryBookTemplate).where(StoryBookTemplate.id == template_id)

        if not include_inactive:
            query = query.where(
                StoryBookTemplate.is_active == True,
                StoryBookTemplate.is_published == True,
            )

        result = await self.db.execute(query)
        template = result.scalar_one_or_none()

        if not template:
            raise NotFoundException(
                message="Story book template not found",
                error_code="STORY_TEMPLATE_NOT_FOUND",
                details={"template_id": str(template_id)},
            )

        return template

    async def get_all(
        self,
        filters: StoryBookTemplateFilters | None = None,
        include_inactive: bool = False,
    ) -> Select[tuple[StoryBookTemplate]]:
        """Get all templates with optional filters - returns query for pagination"""
        query = select(StoryBookTemplate)

        # Base filters
        conditions = []
        if not include_inactive:
            conditions.extend(
                [
                    StoryBookTemplate.is_active == True,
                    StoryBookTemplate.is_published == True,
                ]
            )

        if filters:
            # Genre filter
            if filters.genre:
                conditions.append(StoryBookTemplate.genre == filters.genre)

            # Age group filter
            if filters.age_group:
                conditions.append(StoryBookTemplate.age_group == filters.age_group)

            # Reading level filter
            if filters.reading_level:
                conditions.append(StoryBookTemplate.reading_level == filters.reading_level)

            # Price range filter
            if filters.min_price is not None:
                conditions.append(StoryBookTemplate.price >= filters.min_price)
            if filters.max_price is not None:
                conditions.append(StoryBookTemplate.price <= filters.max_price)

            # Tags filter (contains any of the tags)
            if filters.tags:
                conditions.append(StoryBookTemplate.tags.contains(filters.tags))

            # Full-text search
            if filters.search:
                search_term = f"%{filters.search}%"
                conditions.append(
                    or_(
                        StoryBookTemplate.title.ilike(search_term),
                        StoryBookTemplate.description.ilike(search_term),
                    )
                )

        if conditions:
            query = query.where(and_(*conditions))

        # Sorting
        if filters:
            sort_column = getattr(StoryBookTemplate, filters.sort_by)
            if filters.sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column)
        else:
            query = query.order_by(desc(StoryBookTemplate.created_at))

        return query

    async def create(self, template_data: StoryBookTemplateCreate) -> StoryBookTemplate:
        """Create a new story book template"""
        template = StoryBookTemplate(**template_data.model_dump())
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def update(
        self,
        template_id: UUID,
        template_data: StoryBookTemplateUpdate,
    ) -> StoryBookTemplate:
        """Update a story book template"""
        template = await self.get_by_id(template_id, include_inactive=True)

        # Update only provided fields
        update_data = template_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def delete(self, template_id: UUID) -> None:
        """Soft delete a story book template"""
        template = await self.get_by_id(template_id, include_inactive=True)
        template.is_active = False
        await self.db.commit()

    async def get_by_genre(self, genre: str) -> Sequence[StoryBookTemplate]:
        """Get all templates by genre"""
        query = select(StoryBookTemplate).where(
            StoryBookTemplate.genre == genre,
            StoryBookTemplate.is_active == True,
            StoryBookTemplate.is_published == True,
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_series(self, series_id: UUID) -> Sequence[StoryBookTemplate]:
        """Get all templates in a series"""
        query = (
            select(StoryBookTemplate)
            .where(
                StoryBookTemplate.series_id == series_id,
                StoryBookTemplate.is_active == True,
                StoryBookTemplate.is_published == True,
            )
            .order_by(StoryBookTemplate.book_number)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_genres(self) -> list[str]:
        """Get all unique genres"""
        query = (
            select(StoryBookTemplate.genre)
            .where(
                StoryBookTemplate.is_active == True,
                StoryBookTemplate.is_published == True,
            )
            .distinct()
            .order_by(StoryBookTemplate.genre)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_count(self, filters: StoryBookTemplateFilters | None = None) -> int:
        """Get total count of templates matching filters"""
        query = await self.get_all(filters)
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        return result.scalar_one()
