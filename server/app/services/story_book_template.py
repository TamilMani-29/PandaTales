"""Story Book Template Service - Business Logic Layer"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common import Paginated, paginate
from app.common.logging import get_logger
from app.models.story_book_template import StoryBookTemplate
from app.repositories.story_book_template import StoryBookTemplateRepository
from app.schemas.story_book_template import (
    StoryBookTemplateCreate,
    StoryBookTemplateFilters,
    StoryBookTemplateSeriesInfo,
    StoryBookTemplateUpdate,
)

logger = get_logger(__name__)


class StoryBookTemplateService:
    """Service for story book template business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = StoryBookTemplateRepository(db)

    async def get_template(
        self,
        template_id: UUID,
        include_inactive: bool = False,
    ) -> StoryBookTemplate:
        """Get a single template by ID"""
        logger.info("Fetching story book template", template_id=str(template_id))
        return await self.repository.get_by_id(template_id, include_inactive)

    async def list_templates(
        self,
        filters: StoryBookTemplateFilters | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> Paginated[StoryBookTemplate]:
        """List templates with pagination and filters"""
        logger.info(
            "Listing story book templates",
            page=page,
            limit=limit,
            filters=filters.model_dump() if filters else None,
        )

        query = await self.repository.get_all(filters)
        return await paginate(self.db, query, page, limit)

    async def create_template(
        self, template_data: StoryBookTemplateCreate
    ) -> StoryBookTemplate:
        """Create a new story book template"""
        logger.info("Creating story book template", title=template_data.title)

        # Validate series logic
        if template_data.book_type == "series":
            if not template_data.series_id and template_data.book_number != 1:
                raise ValueError("First book in series must have book_number=1")

        template = await self.repository.create(template_data)

        logger.info("Story book template created", template_id=str(template.id))
        return template

    async def update_template(
        self,
        template_id: UUID,
        template_data: StoryBookTemplateUpdate,
    ) -> StoryBookTemplate:
        """Update an existing template"""
        logger.info("Updating story book template", template_id=str(template_id))

        template = await self.repository.update(template_id, template_data)

        logger.info("Story book template updated", template_id=str(template.id))
        return template

    async def delete_template(self, template_id: UUID) -> None:
        """Soft delete a template"""
        logger.info("Deleting story book template", template_id=str(template_id))

        await self.repository.delete(template_id)

        logger.info("Story book template deleted", template_id=str(template_id))

    async def get_templates_by_genre(self, genre: str) -> list[StoryBookTemplate]:
        """Get all templates for a specific genre"""
        logger.info("Fetching story book templates by genre", genre=genre)
        return list(await self.repository.get_by_genre(genre))

    async def get_series_templates(self, series_id: UUID) -> list[StoryBookTemplate]:
        """Get all templates in a series"""
        logger.info("Fetching series templates", series_id=str(series_id))
        return list(await self.repository.get_by_series(series_id))

    async def get_series_info(
        self, series_id: UUID
    ) -> StoryBookTemplateSeriesInfo | None:
        """Get series information with all books"""
        templates = await self.get_series_templates(series_id)

        if not templates:
            return None

        # First template is the series parent
        series_template = templates[0]

        return StoryBookTemplateSeriesInfo(
            series_id=series_id,
            series_title=series_template.title,
            book_count=len(templates),
            books=templates,
        )

    async def get_all_genres(self) -> list[str]:
        """Get list of all unique genres"""
        logger.info("Fetching all genres")
        return await self.repository.get_genres()
