"""Generated Book Service"""

from datetime import datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ForbiddenException, NotFoundException
from app.common.logging import get_logger
from app.common.pagination import PaginationParams
from app.models.coloring_book_template import ColoringBookTemplate
from app.models.generated_book import GeneratedBook
from app.models.story_book_template import StoryBookTemplate
from app.repositories.child_profile import ChildProfileRepository
from app.repositories.coloring_book_template import ColoringBookTemplateRepository
from app.repositories.generated_book import GeneratedBookRepository
from app.repositories.generation_config import GenerationConfigRepository
from app.repositories.story_book_template import StoryBookTemplateRepository
from app.schemas.generated_book import (
    BookGenerationCreate,
    BookGenerationResponse,
    BookPage,
    ChildInfo,
    GeneratedBookFilters,
    GeneratedBookListItem,
    GeneratedBookResponse,
    GenerationErrorDetail,
    GenerationStatusCancelled,
    GenerationStatusCompleted,
    GenerationStatusFailed,
    GenerationStatusProcessing,
    GenerationStatusQueued,
    GenerationStepStatus,
    PhotoToColoringGenerationCreate,
    TemplateInfo,
    ThemeBasedGenerationCreate,
)
from app.services.mock_generation import start_mock_generation

logger = get_logger(__name__)


class GeneratedBookService:
    """Service for generated book business logic"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = GeneratedBookRepository(db)
        self.story_template_repo = StoryBookTemplateRepository(db)
        self.coloring_template_repo = ColoringBookTemplateRepository(db)
        self.child_profile_repo = ChildProfileRepository(db)
        self.config_repo = GenerationConfigRepository(db)

    async def _get_child_data(
        self, child_id: UUID | None, child_name: str | None, child_age: int | None,
        child_gender: str | None, user_id: UUID
    ) -> tuple[str, int, str, UUID | None]:
        """Helper method to get or validate child data"""
        if child_id:
            child = await self.child_profile_repo.get_by_id(child_id, user_id)
            if not child:
                raise NotFoundException("Child profile not found")
            return child.name, child.age, child.gender, child_id
        else:
            if not child_name or not child_age:
                raise ValueError("Child information is required")
            return child_name, child_age, child_gender or "other", None

    async def _check_generation_limit(self, user_id: UUID, max_per_day: int = 10) -> None:
        """Check if user has exceeded daily generation limit"""
        daily_count = await self.repository.get_user_generation_count_today(user_id)
        logger.info("checking_generation_limit", user_id=str(user_id), daily_count=daily_count, max_per_day=max_per_day)
        if daily_count >= max_per_day:
            logger.warning("generation_limit_exceeded", user_id=str(user_id), daily_count=daily_count)
            raise ForbiddenException("Daily generation limit exceeded")

    async def initiate_photo_to_coloring_generation(
        self,
        user_id: UUID,
        data: PhotoToColoringGenerationCreate,
        photos: list[str],  # 1-10 uploaded photo URLs
    ) -> BookGenerationResponse:
        """Initiate photo-to-coloring generation (direct photo conversion)"""
        logger.info("initiating_photo_to_coloring", user_id=str(user_id), photo_count=len(photos))
        await self._check_generation_limit(user_id)

        # Validate photos (1-10 for photo-to-coloring)
        if not photos or len(photos) < 1:
            raise ValueError("At least 1 photo is required")
        if len(photos) > 10:
            raise ValueError("Maximum 10 photos allowed for photo-to-coloring")

        # Get child data
        child_name, child_age, child_gender, child_id = await self._get_child_data(
            data.child_id, data.child_name, data.child_age, data.child_gender, user_id
        )

        # Get current queue position
        queued_books = await self.repository.get_by_status("queued")
        queue_position = len(queued_books) + 1

        # Create a synthetic template_id (we're not using a template)
        # In production, you might create a "photo-to-coloring" template record
        from uuid import uuid4
        template_id = uuid4()  # Placeholder

        # Create generation record
        book = GeneratedBook(
            user_id=user_id,
            template_type="coloring_book",
            template_id=template_id,
            generation_type="photo_to_coloring",
            child_id=child_id,
            child_name=child_name,
            child_age=child_age,
            child_gender=child_gender,
            status="queued",
            progress=0,
            queue_position=queue_position,
            estimated_completion_time=120,  # 2 minutes estimate
            photos=photos,
            parent_email=data.parent_email,
            generation_steps={
                "photo_processing": "pending",
                "line_extraction": "pending",
                "edge_detection": "pending",
                "coloring_page_creation": "pending",
            },
        )

        book = await self.repository.create(book)
        await self.db.commit()

        # Start mock generation in background (replace with actual AI generation later)
        await start_mock_generation(book.id, self.db)

        return BookGenerationResponse(
            generation_id=book.id,
            status="queued",
            estimated_time=120,
            queue_position=queue_position,
        )

    async def initiate_theme_based_generation(
        self,
        user_id: UUID,
        data: ThemeBasedGenerationCreate,
        photos: list[str],  # 1-20 photos for theme extraction
    ) -> BookGenerationResponse:
        """Initiate theme-based coloring book generation"""
        await self._check_generation_limit(user_id)

        # Get and validate theme configuration
        theme_config = await self.config_repo.get_by_id(data.theme_config_id)
        if not theme_config or theme_config.config_type != "theme":
            raise NotFoundException("Theme configuration not found")
        if not theme_config.is_active:
            raise ForbiddenException("This theme is not currently available")

        # Validate photos based on theme config
        if not photos or len(photos) < theme_config.min_photos:
            raise ValueError(f"At least {theme_config.min_photos} photos are required for this theme")
        if len(photos) > theme_config.max_photos:
            raise ValueError(f"Maximum {theme_config.max_photos} photos allowed for this theme")

        # Get child data
        child_name, child_age, child_gender, child_id = await self._get_child_data(
            data.child_id, data.child_name, data.child_age, data.child_gender, user_id
        )

        # Get current queue position
        queued_books = await self.repository.get_by_status("queued")
        queue_position = len(queued_books) + 1

        # Estimate time based on number of pages (more pages = more time)
        estimated_time = 60 + (data.num_pages * 10)  # Base 60s + 10s per page

        # Create a synthetic template_id
        from uuid import uuid4
        template_id = uuid4()  # Placeholder

        # Create generation record
        book = GeneratedBook(
            user_id=user_id,
            template_type="coloring_book",
            template_id=template_id,
            generation_type="theme_based",
            theme_config_id=data.theme_config_id,
            selected_theme_name=theme_config.display_name,
            child_id=child_id,
            child_name=child_name,
            child_age=child_age,
            child_gender=child_gender,
            status="queued",
            progress=0,
            queue_position=queue_position,
            estimated_completion_time=estimated_time,
            total_pages=data.num_pages,
            photos=photos,
            parent_email=data.parent_email,
            generation_steps={
                "photo_processing": "pending",
                "theme_extraction": "pending",
                "content_generation": "pending",
                "coloring_page_creation": "pending",
            },
        )

        book = await self.repository.create(book)

        # Increment theme usage count
        await self.config_repo.increment_usage(data.theme_config_id)

        await self.db.commit()

        # Start mock generation in background (replace with actual AI generation later)
        await start_mock_generation(book.id, self.db)

        return BookGenerationResponse(
            generation_id=book.id,
            status="queued",
            estimated_time=estimated_time,
            queue_position=queue_position,
        )

    async def initiate_generation(
        self,
        user_id: UUID,
        data: BookGenerationCreate,
        photos: list[str],  # List of uploaded photo URLs
    ) -> BookGenerationResponse:
        """Initiate book generation process"""
        # Validate generation limit (e.g., max 10 per day)
        daily_count = await self.repository.get_user_generation_count_today(user_id)
        if daily_count >= 10:
            raise ForbiddenException("Daily generation limit exceeded")

        # Get template to validate
        if data.template_type == "story_book":
            template = await self.story_template_repo.get_by_id(data.template_id)
        else:
            template = await self.coloring_template_repo.get_by_id(data.template_id)

        if not template or not template.is_active or not template.is_published:
            raise NotFoundException("Template not found or not available")

        # Get child data
        if data.child_id:
            child = await self.child_profile_repo.get_by_id(data.child_id, user_id)
            if not child:
                raise NotFoundException("Child profile not found")
            child_name = child.name
            child_age = child.age
            child_gender = child.gender
        else:
            child_name = data.child_name  # type: ignore
            child_age = data.child_age  # type: ignore
            child_gender = data.child_gender  # type: ignore

        # Validate photos
        if not photos or len(photos) == 0:
            raise ValueError("At least one photo is required")
        if len(photos) > 3:
            raise ValueError("Maximum 3 photos allowed")

        # Get current queue position
        queued_books = await self.repository.get_by_status("queued")
        queue_position = len(queued_books) + 1

        # Create generation record
        book = GeneratedBook(
            user_id=user_id,
            template_type=data.template_type,
            template_id=data.template_id,
            child_id=data.child_id,
            child_name=child_name,
            child_age=child_age,
            child_gender=child_gender,
            status="queued",
            progress=0,
            queue_position=queue_position,
            estimated_completion_time=180,  # 3 minutes estimate
            photos=photos,
            parent_email=data.parent_email,
            generation_steps={
                "photo_processing": "pending",
                "story_generation": "pending",
                "image_generation": "pending",
                "pdf_generation": "pending",
            },
        )

        book = await self.repository.create(book)
        await self.db.commit()

        # Start mock generation in background (replace with actual AI generation later)
        await start_mock_generation(book.id, self.db)

        return BookGenerationResponse(
            generation_id=book.id,
            status="queued",
            estimated_time=180,
            queue_position=queue_position,
        )

    async def get_generation_status(
        self, generation_id: UUID, user_id: UUID
    ) -> (
        GenerationStatusQueued
        | GenerationStatusProcessing
        | GenerationStatusCompleted
        | GenerationStatusFailed
        | GenerationStatusCancelled
    ):
        """Get generation status"""
        book = await self.repository.get_by_id(generation_id, user_id)
        if not book:
            raise NotFoundException("Generation not found")

        if book.status == "queued":
            queue_position = await self.repository.get_queued_position(generation_id)
            estimated_wait = queue_position * 180  # Estimate 3 min per book

            return GenerationStatusQueued(
                generation_id=book.id,
                status="queued",
                queue_position=queue_position,
                estimated_wait_time=estimated_wait,
                created_at=book.created_at,
            )

        elif book.status == "processing":
            steps_data = book.generation_steps or {}
            steps = GenerationStepStatus(
                photo_processing=steps_data.get("photo_processing", "pending"),
                story_generation=steps_data.get("story_generation", "pending"),
                image_generation=steps_data.get("image_generation", "pending"),
                pdf_generation=steps_data.get("pdf_generation", "pending"),
            )

            return GenerationStatusProcessing(
                generation_id=book.id,
                status="processing",
                progress=book.progress,
                current_step=book.current_step or "Processing",
                steps=steps,
                estimated_completion_time=book.estimated_completion_time or 120,
            )

        elif book.status == "completed":
            preview_url = f"/preview/{book.id}"

            return GenerationStatusCompleted(
                generation_id=book.id,
                status="completed",
                book_id=book.id,
                progress=100,
                completed_at=book.completed_at or book.updated_at,
                preview_url=preview_url,
            )

        elif book.status == "failed":
            error = GenerationErrorDetail(
                code=book.error_code or "GENERATION_ERROR",
                message=book.error_message or "Generation failed",
                details=book.error_details,
            )

            return GenerationStatusFailed(
                generation_id=book.id,
                status="failed",
                error=error,
                failed_at=book.failed_at or book.updated_at,
            )

        else:  # cancelled
            return GenerationStatusCancelled(
                generation_id=book.id,
                status="cancelled",
                cancelled_at=book.updated_at,
            )

    async def cancel_generation(self, generation_id: UUID, user_id: UUID) -> None:
        """Cancel a generation"""
        book = await self.repository.get_by_id(generation_id, user_id)
        if not book:
            raise NotFoundException("Generation not found")

        if book.status in ["completed", "failed", "cancelled"]:
            raise ForbiddenException("Cannot cancel completed or failed generation")

        await self.repository.update_status(generation_id, "cancelled")
        await self.db.commit()

    async def list_generated_books(
        self,
        user_id: UUID,
        filters: GeneratedBookFilters | None = None,
        pagination: PaginationParams | None = None,
    ) -> tuple[Sequence[GeneratedBookListItem], int]:
        """List user's generated books"""
        books, total = await self.repository.get_all(user_id, filters, pagination)

        # Convert to list items
        items = []
        for book in books:
            # Get template title
            if book.template_type == "story_book":
                template = await self.story_template_repo.get_by_id(book.template_id)
            else:
                template = await self.coloring_template_repo.get_by_id(book.template_id)

            template_title = template.title if template else "Unknown Template"

            # Generate URLs
            preview_url = f"/preview/{book.id}" if book.status == "completed" else None
            download_url = (
                f"/books/{book.id}/download"
                if book.is_purchased and book.status == "completed"
                else None
            )

            items.append(
                GeneratedBookListItem(
                    id=book.id,
                    template_id=book.template_id,
                    template_type=book.template_type,
                    template_title=template_title,
                    child_name=book.child_name,
                    child_id=book.child_id,
                    status=book.status,
                    cover_image_url=book.cover_image_url,
                    is_purchased=book.is_purchased,
                    purchased_at=book.purchased_at,
                    generated_at=book.created_at,
                    completed_at=book.completed_at,
                    preview_url=preview_url,
                    download_url=download_url,
                )
            )

        return items, total

    async def get_book_details(
        self, book_id: UUID, user_id: UUID
    ) -> GeneratedBookResponse:
        """Get generated book details"""
        book = await self.repository.get_by_id(book_id, user_id)
        if not book:
            raise NotFoundException("Book not found")

        # Get template info
        if book.template_type == "story_book":
            template = await self.story_template_repo.get_by_id(book.template_id)
            template_info = TemplateInfo(
                title=template.title if template else "Unknown",
                genre=template.genre if template else None,
                theme=None,
                age_group=template.age_group if template else "Unknown",
            )
        else:
            template = await self.coloring_template_repo.get_by_id(book.template_id)
            template_info = TemplateInfo(
                title=template.title if template else "Unknown",
                genre=None,
                theme=template.theme if template else None,
                age_group=template.age_group if template else "Unknown",
            )

        # Child info
        child_info = ChildInfo(
            id=book.child_id,
            name=book.child_name,
            age=book.child_age,
            gender=book.child_gender,
        )

        # Preview pages
        preview_pages = None
        if book.preview_pages:
            preview_pages = [BookPage(**page) for page in book.preview_pages]

        return GeneratedBookResponse(
            id=book.id,
            template_id=book.template_id,
            template_type=book.template_type,
            template=template_info,
            child=child_info,
            status=book.status,
            is_purchased=book.is_purchased,
            cover_image_url=book.cover_image_url,
            total_pages=book.total_pages,
            preview_pages=preview_pages,
            generated_at=book.created_at,
            completed_at=book.completed_at,
            generation_duration=book.generation_duration,
            progress=book.progress,
        )

    async def delete_book(self, book_id: UUID, user_id: UUID) -> None:
        """Delete a generated book"""
        book = await self.repository.get_by_id(book_id, user_id)
        if not book:
            raise NotFoundException("Book not found")

        if book.is_purchased:
            raise ForbiddenException("Cannot delete purchased books")

        await self.repository.delete(book)
        await self.db.commit()

    async def regenerate_book(
        self, book_id: UUID, user_id: UUID
    ) -> BookGenerationResponse:
        """Regenerate a book with the same parameters"""
        old_book = await self.repository.get_by_id(book_id, user_id)
        if not old_book:
            raise NotFoundException("Book not found")

        # Create new generation request with same params
        data = BookGenerationCreate(
            template_id=old_book.template_id,
            template_type=old_book.template_type,
            child_id=old_book.child_id,
            child_name=old_book.child_name if not old_book.child_id else None,
            child_age=old_book.child_age if not old_book.child_id else None,
            child_gender=old_book.child_gender if not old_book.child_id else None,
            parent_email=old_book.parent_email,
        )

        return await self.initiate_generation(user_id, data, old_book.photos)
