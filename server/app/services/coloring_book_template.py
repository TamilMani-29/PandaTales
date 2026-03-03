"""Coloring Book Template Service - Business Logic Layer"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common import Paginated, paginate
from app.common.logging import get_logger
from app.models.coloring_book_template import ColoringBookTemplate
from app.repositories.coloring_book_template import ColoringBookTemplateRepository
from app.schemas.coloring_book_template import (
    ColoringBookTemplateCreate,
    ColoringBookTemplateFilters,
    ColoringBookTemplateUpdate,
)

logger = get_logger(__name__)


class ColoringBookTemplateService:
    """Service for coloring book template business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ColoringBookTemplateRepository(db)

    async def get_template(
        self,
        template_id: UUID,
        include_inactive: bool = False,
    ) -> ColoringBookTemplate:
        """Get a single template by ID"""
        logger.info("Fetching coloring book template", template_id=str(template_id))
        return await self.repository.get_by_id(template_id, include_inactive)

    async def list_templates(
        self,
        filters: ColoringBookTemplateFilters | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> Paginated[ColoringBookTemplate]:
        """List templates with pagination and filters"""
        logger.info(
            "Listing coloring book templates",
            page=page,
            limit=limit,
            filters=filters.model_dump() if filters else None,
        )

        query = await self.repository.get_all(filters)
        return await paginate(self.db, query, page, limit)

    async def create_template(
        self, template_data: ColoringBookTemplateCreate
    ) -> ColoringBookTemplate:
        """Create a new coloring book template"""
        logger.info("Creating coloring book template", title=template_data.title)

        template = await self.repository.create(template_data)

        logger.info("Coloring book template created", template_id=str(template.id))
        return template

    async def update_template(
        self,
        template_id: UUID,
        template_data: ColoringBookTemplateUpdate,
    ) -> ColoringBookTemplate:
        """Update an existing template"""
        logger.info("Updating coloring book template", template_id=str(template_id))

        template = await self.repository.update(template_id, template_data)

        logger.info("Coloring book template updated", template_id=str(template.id))
        return template

    async def delete_template(self, template_id: UUID) -> None:
        """Soft delete a template"""
        logger.info("Deleting coloring book template", template_id=str(template_id))

        await self.repository.delete(template_id)

        logger.info("Coloring book template deleted", template_id=str(template_id))

    async def get_templates_by_theme(self, theme: str) -> list[ColoringBookTemplate]:
        """Get all templates for a specific theme"""
        logger.info("Fetching coloring book templates by theme", theme=theme)
        return list(await self.repository.get_by_theme(theme))

    async def get_all_themes(self) -> list[str]:
        """Get list of all unique themes"""
        logger.info("Fetching all themes")
        return await self.repository.get_themes()
