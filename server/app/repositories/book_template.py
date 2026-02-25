"""Book Template Repository - Data Access Layer"""

from typing import Sequence
from uuid import UUID

from sqlalchemy import Select, and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundException
from app.models.book_template import BookTemplate
from app.schemas.book_template import BookTemplateCreate, BookTemplateFilters, BookTemplateUpdate


class BookTemplateRepository:
    """Repository for book template data access"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, template_id: UUID, include_inactive: bool = False) -> BookTemplate:
        """Get template by ID"""
        query = select(BookTemplate).where(BookTemplate.id == template_id)

        if not include_inactive:
            query = query.where(
                BookTemplate.is_active == True,
                BookTemplate.is_published == True,
            )

        result = await self.db.execute(query)
        template = result.scalar_one_or_none()

        if not template:
            raise NotFoundException(
                message="Book template not found",
                error_code="TEMPLATE_NOT_FOUND",
                details={"template_id": str(template_id)},
            )

        return template

    async def get_all(
        self,
        filters: BookTemplateFilters | None = None,
        include_inactive: bool = False,
    ) -> Select[tuple[BookTemplate]]:
        """Get all templates with optional filters - returns query for pagination"""
        query = select(BookTemplate)

        # Base filters
        conditions = []
        if not include_inactive:
            conditions.extend(
                [
                    BookTemplate.is_active == True,
                    BookTemplate.is_published == True,
                ]
            )

        if filters:
            # Template type filter
            if filters.template_type:
                conditions.append(BookTemplate.template_type == filters.template_type)

            # Genre filter
            if filters.genre:
                conditions.append(BookTemplate.genre == filters.genre)

            # Age group filter
            if filters.age_group:
                conditions.append(BookTemplate.age_group == filters.age_group)

            # Difficulty filter
            if filters.difficulty:
                conditions.append(BookTemplate.difficulty == filters.difficulty)

            # Price range filter
            if filters.min_price is not None:
                conditions.append(BookTemplate.price >= filters.min_price)
            if filters.max_price is not None:
                conditions.append(BookTemplate.price <= filters.max_price)

            # Tags filter (contains any of the tags)
            if filters.tags:
                conditions.append(BookTemplate.tags.contains(filters.tags))

            # Full-text search
            if filters.search:
                search_term = f"%{filters.search}%"
                conditions.append(
                    or_(
                        BookTemplate.title.ilike(search_term),
                        BookTemplate.description.ilike(search_term),
                    )
                )

        if conditions:
            query = query.where(and_(*conditions))

        # Sorting
        if filters:
            sort_column = getattr(BookTemplate, filters.sort_by)
            if filters.sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column)
        else:
            query = query.order_by(desc(BookTemplate.created_at))

        return query

    async def create(self, template_data: BookTemplateCreate) -> BookTemplate:
        """Create a new book template"""
        template = BookTemplate(**template_data.model_dump())
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def update(
        self,
        template_id: UUID,
        template_data: BookTemplateUpdate,
    ) -> BookTemplate:
        """Update a book template"""
        template = await self.get_by_id(template_id, include_inactive=True)

        # Update only provided fields
        update_data = template_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def delete(self, template_id: UUID) -> None:
        """Soft delete a book template"""
        template = await self.get_by_id(template_id, include_inactive=True)
        template.is_active = False
        await self.db.commit()

    async def get_by_genre(self, genre: str) -> Sequence[BookTemplate]:
        """Get all templates by genre"""
        query = select(BookTemplate).where(
            BookTemplate.genre == genre,
            BookTemplate.is_active == True,
            BookTemplate.is_published == True,
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_series(self, series_id: UUID) -> Sequence[BookTemplate]:
        """Get all templates in a series"""
        query = (
            select(BookTemplate)
            .where(
                BookTemplate.series_id == series_id,
                BookTemplate.is_active == True,
                BookTemplate.is_published == True,
            )
            .order_by(BookTemplate.book_number)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_genres(self) -> list[str]:
        """Get all unique genres"""
        query = (
            select(BookTemplate.genre)
            .where(
                BookTemplate.is_active == True,
                BookTemplate.is_published == True,
            )
            .distinct()
            .order_by(BookTemplate.genre)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_count(self, filters: BookTemplateFilters | None = None) -> int:
        """Get total count of templates matching filters"""
        query = await self.get_all(filters)
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        return result.scalar_one()
