"""Book Template Service - Business Logic Layer"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common import Paginated, paginate
from app.common.logging import get_logger
from app.models.book_template import BookTemplate
from app.repositories.book_template import BookTemplateRepository
from app.schemas.book_template import (
    BookTemplateCreate,
    BookTemplateFilters,
    BookTemplateSeriesInfo,
    BookTemplateUpdate,
)

logger = get_logger(__name__)


class BookTemplateService:
    """Service for book template business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = BookTemplateRepository(db)

    async def get_template(
        self,
        template_id: UUID,
        include_inactive: bool = False,
    ) -> BookTemplate:
        """Get a single template by ID"""
        logger.info("Fetching template", template_id=str(template_id))
        return await self.repository.get_by_id(template_id, include_inactive)

    async def list_templates(
        self,
        filters: BookTemplateFilters | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> Paginated[BookTemplate]:
        """List templates with pagination and filters"""
        logger.info(
            "Listing templates",
            page=page,
            limit=limit,
            filters=filters.model_dump() if filters else None,
        )

        query = await self.repository.get_all(filters)
        return await paginate(self.db, query, page, limit)

    async def create_template(self, template_data: BookTemplateCreate) -> BookTemplate:
        """Create a new book template"""
        logger.info("Creating template", title=template_data.title)

        # Validate series logic
        if template_data.book_type == "series":
            if not template_data.series_id and template_data.book_number != 1:
                raise ValueError("First book in series must have book_number=1")

        template = await self.repository.create(template_data)

        logger.info("Template created", template_id=str(template.id))
        return template

    async def update_template(
        self,
        template_id: UUID,
        template_data: BookTemplateUpdate,
    ) -> BookTemplate:
        """Update an existing template"""
        logger.info("Updating template", template_id=str(template_id))

        template = await self.repository.update(template_id, template_data)

        logger.info("Template updated", template_id=str(template.id))
        return template

    async def delete_template(self, template_id: UUID) -> None:
        """Soft delete a template"""
        logger.info("Deleting template", template_id=str(template_id))

        await self.repository.delete(template_id)

        logger.info("Template deleted", template_id=str(template_id))

    async def get_templates_by_genre(self, genre: str) -> list[BookTemplate]:
        """Get all templates for a specific genre"""
        logger.info("Fetching templates by genre", genre=genre)
        return list(await self.repository.get_by_genre(genre))

    async def get_series_templates(self, series_id: UUID) -> list[BookTemplate]:
        """Get all templates in a series"""
        logger.info("Fetching series templates", series_id=str(series_id))
        return list(await self.repository.get_by_series(series_id))

    async def get_series_info(self, series_id: UUID) -> BookTemplateSeriesInfo | None:
        """Get series information with all books"""
        templates = await self.get_series_templates(series_id)

        if not templates:
            return None

        # First template is the series parent
        series_template = templates[0]

        return BookTemplateSeriesInfo(
            series_id=series_id,
            series_title=series_template.title,
            book_count=len(templates),
            books=templates,
        )

    async def get_all_genres(self) -> list[str]:
        """Get list of all unique genres"""
        logger.info("Fetching all genres")
        return await self.repository.get_genres()
