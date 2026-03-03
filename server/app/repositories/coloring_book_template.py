"""Coloring Book Template Repository - Data Access Layer"""

from typing import Sequence
from uuid import UUID

from sqlalchemy import Select, and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundException
from app.models.coloring_book_template import ColoringBookTemplate
from app.schemas.coloring_book_template import (
    ColoringBookTemplateCreate,
    ColoringBookTemplateFilters,
    ColoringBookTemplateUpdate,
)


class ColoringBookTemplateRepository:
    """Repository for coloring book template data access"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self, template_id: UUID, include_inactive: bool = False
    ) -> ColoringBookTemplate:
        """Get template by ID"""
        query = select(ColoringBookTemplate).where(ColoringBookTemplate.id == template_id)

        if not include_inactive:
            query = query.where(
                ColoringBookTemplate.is_active == True,
                ColoringBookTemplate.is_published == True,
            )

        result = await self.db.execute(query)
        template = result.scalar_one_or_none()

        if not template:
            raise NotFoundException(
                message="Coloring book template not found",
                error_code="COLORING_TEMPLATE_NOT_FOUND",
                details={"template_id": str(template_id)},
            )

        return template

    async def get_all(
        self,
        filters: ColoringBookTemplateFilters | None = None,
        include_inactive: bool = False,
    ) -> Select[tuple[ColoringBookTemplate]]:
        """Get all templates with optional filters - returns query for pagination"""
        query = select(ColoringBookTemplate)

        # Base filters
        conditions = []
        if not include_inactive:
            conditions.extend(
                [
                    ColoringBookTemplate.is_active == True,
                    ColoringBookTemplate.is_published == True,
                ]
            )

        if filters:
            # Theme filter
            if filters.theme:
                conditions.append(ColoringBookTemplate.theme == filters.theme)

            # Age group filter
            if filters.age_group:
                conditions.append(ColoringBookTemplate.age_group == filters.age_group)

            # Price range filter
            if filters.min_price is not None:
                conditions.append(ColoringBookTemplate.price >= filters.min_price)
            if filters.max_price is not None:
                conditions.append(ColoringBookTemplate.price <= filters.max_price)

            # Tags filter (contains any of the tags)
            if filters.tags:
                conditions.append(ColoringBookTemplate.tags.contains(filters.tags))

            # Full-text search
            if filters.search:
                search_term = f"%{filters.search}%"
                conditions.append(
                    or_(
                        ColoringBookTemplate.title.ilike(search_term),
                        ColoringBookTemplate.description.ilike(search_term),
                    )
                )

        if conditions:
            query = query.where(and_(*conditions))

        # Sorting
        if filters:
            sort_column = getattr(ColoringBookTemplate, filters.sort_by)
            if filters.sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column)
        else:
            query = query.order_by(desc(ColoringBookTemplate.created_at))

        return query

    async def create(
        self, template_data: ColoringBookTemplateCreate
    ) -> ColoringBookTemplate:
        """Create a new coloring book template"""
        template = ColoringBookTemplate(**template_data.model_dump())
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def update(
        self,
        template_id: UUID,
        template_data: ColoringBookTemplateUpdate,
    ) -> ColoringBookTemplate:
        """Update a coloring book template"""
        template = await self.get_by_id(template_id, include_inactive=True)

        # Update only provided fields
        update_data = template_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def delete(self, template_id: UUID) -> None:
        """Soft delete a coloring book template"""
        template = await self.get_by_id(template_id, include_inactive=True)
        template.is_active = False
        await self.db.commit()

    async def get_by_theme(self, theme: str) -> Sequence[ColoringBookTemplate]:
        """Get all templates by theme"""
        query = select(ColoringBookTemplate).where(
            ColoringBookTemplate.theme == theme,
            ColoringBookTemplate.is_active == True,
            ColoringBookTemplate.is_published == True,
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_themes(self) -> list[str]:
        """Get all unique themes"""
        query = (
            select(ColoringBookTemplate.theme)
            .where(
                ColoringBookTemplate.is_active == True,
                ColoringBookTemplate.is_published == True,
            )
            .distinct()
            .order_by(ColoringBookTemplate.theme)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_count(self, filters: ColoringBookTemplateFilters | None = None) -> int:
        """Get total count of templates matching filters"""
        query = await self.get_all(filters)
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        return result.scalar_one()
