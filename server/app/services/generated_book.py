"""Generated Book Service"""

import asyncio
import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ForbiddenException, NotFoundException
from app.common.logging import get_logger
from app.common.pagination import PaginationParams
from app.core.config import settings
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
from app.services.replicate_generation import ReplicateGenerationService

logger = get_logger(__name__)


async def _run_replicate_generation(
    book_id: UUID,
    reference_photo_object: str,
    prompts_config: dict,
    child_name: str,
    child_gender: str,
) -> None:
    """Background coroutine: start all Replicate predictions for a story book.

    Opens its own DB session so it's not tied to the request session that
    gets closed as soon as the HTTP response is sent.
    """
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            svc = ReplicateGenerationService(db)
            await svc.start_story_book_generation(book_id, reference_photo_object, prompts_config, child_name, child_gender)
            await db.commit()
            logger.info("replicate_generation_started", book_id=str(book_id))
        except Exception as exc:
            logger.error("replicate_generation_background_error", book_id=str(book_id), error=str(exc))


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
            whatsapp_number=data.whatsapp_number,
            selected_theme_name=data.selected_theme_name,
            generation_steps={
                "photo_processing": "pending",
                "line_extraction": "pending",
                "edge_detection": "pending",
                "coloring_page_creation": "pending",
            },
        )

        book = await self.repository.create(book)
        await self.db.commit()

        try:
            await self._send_personalized_started_email(
                parent_email=data.parent_email,
                child_name=child_name,
                selected_theme_name=data.selected_theme_name,
            )
        except Exception as exc:
            logger.warning(
                "personalized_start_email_failed",
                generation_id=str(book.id),
                parent_email=data.parent_email,
                error=str(exc),
            )

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
            whatsapp_number=data.whatsapp_number,
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
        # Validate generation limit (increased for testing)
        daily_count = await self.repository.get_user_generation_count_today(user_id)
        if daily_count >= 100:
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
            whatsapp_number=data.whatsapp_number,
            generation_steps={
                "photo_processing": "pending",
                "story_generation": "pending",
                "image_generation": "pending",
                "pdf_generation": "pending",
            },
        )

        book = await self.repository.create(book)
        await self.db.commit()

        # Dispatch generation: real Replicate for story books, mock for coloring books
        if data.template_type == "story_book" and hasattr(template, "prompts_config") and template.prompts_config:
            # Use the first uploaded photo as the reference image
            reference_photo = photos[0]
            asyncio.ensure_future(
                _run_replicate_generation(
                    book.id, reference_photo, template.prompts_config, child_name, data.child_gender
                )
            )
        else:
            # Coloring books still use mock generation until real pipeline is ready
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
            # For story books with Replicate predictions, poll and update in real time
            if book.template_type == "story_book" and book.replicate_prediction_ids:
                replicate_svc = ReplicateGenerationService(self.db)
                poll_result = await replicate_svc.poll_and_update(generation_id)
                await self.db.commit()
                # Re-fetch updated book after polling
                book = await self.repository.get_by_id(generation_id, user_id)
                if book and book.status == "completed":
                    preview_url = f"/preview/{book.id}"
                    return GenerationStatusCompleted(
                        generation_id=book.id,
                        status="completed",
                        book_id=book.id,
                        progress=100,
                        completed_at=book.completed_at or book.updated_at,
                        preview_url=preview_url,
                    )
                if book and book.status == "failed":
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

        # For story books with Replicate predictions, always poll to ensure images are downloaded
        # Even if status is "completed", we need to retry failed image downloads
        if (
            book.template_type == "story_book"
            and book.replicate_prediction_ids
            and book.status in ("processing", "completed")  # Poll for both states
        ):
            replicate_svc = ReplicateGenerationService(self.db)
            await replicate_svc.poll_and_update(book_id)
            await self.db.commit()
            # Re-fetch to get the updated status / preview_pages
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

    async def _send_personalized_started_email(
        self,
        *,
        parent_email: str,
        child_name: str,
        selected_theme_name: str | None,
    ) -> None:
        if not settings.SMTP_HOST or not settings.SMTP_PORT:
            return
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            return

        parent_name = self._guess_parent_name(parent_email)

        message = EmailMessage()
        message["Subject"] = "✨ Your book is ready! Download now | Pandora Pages"
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = parent_email
        message.set_content(
            f"Hi {parent_name} 👋\n\n"
            "You just made a child's day - maybe even their whole week.\n\n"
            "Your book is ready right now. No waiting. No shipping. Just pure magic.\n\n"
            "⬇️ Download Your Book Now\n"
            "(Attached as PDF in this email)\n\n"
            '"Every page read tonight plants a seed - for curiosity, courage, and a lifelong love of learning." 🌱\n\n'
            "- Team PandoraPages\n\n"
            "✨ Make it extra special\n\n"
            "🖨️ Print and bind it\n"
            "Turn this into a real book.\n"
            "Any nearby print shop can spiral-bind it for just INR 100-INR 150.\n\n"
            "📸 Capture the moment\n"
            "Seeing a child connect with their own story is priceless.\n"
            "Tag us on Instagram: @PandoraPages.in\n\n"
            "🎁 Share the joy\n"
            "Know another parent who'd love this?\n"
            "Forward this email - it might make their child's day too.\n\n"
            "🎨 You might also love\n"
            "- PersonaColor Book (now just INR 129)\n"
            "- 21-Day SkillSprint (now just INR 99)\n"
            "- LifePath Board Game (now just INR 149)\n\n"
            "All available instantly - download and print at home.\n\n"
            "🎁 Share and Earn\n"
            "Share your code with 5 parents and get a FREE digital book.\n\n"
            "📱 Join Our Parent Community\n"
            "Free coloring pages, mini-stories and activity ideas every week.\n\n"
            "We'd love to hear how it goes 💛\n\n"
            "With love,\n"
            "PandoraPages"
        )

        await asyncio.to_thread(self._send_email_sync, message)

    @staticmethod
    def _guess_parent_name(email: str) -> str:
        local = (email or "").split("@", 1)[0].strip()
        if not local:
            return "Parent"
        cleaned = local.replace(".", " ").replace("_", " ").replace("-", " ")
        return " ".join(part.capitalize() for part in cleaned.split() if part) or "Parent"

    @staticmethod
    def _send_email_sync(message: EmailMessage) -> None:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
