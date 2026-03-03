"""Mock Generation Service - Simulates AI book generation"""

import asyncio
import io
import json
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.logging import get_logger
from app.repositories.generated_book import GeneratedBookRepository
from app.services.storage import StorageService

logger = get_logger(__name__)


class MockContentGenerator:
    """Generate mock content for testing"""

    @staticmethod
    def generate_mock_cover_image(
        child_name: str,
        template_type: str,
        width: int = 800,
        height: int = 1000,
    ) -> bytes:
        """Generate a mock cover image"""
        # Create a colorful gradient background
        image = Image.new("RGB", (width, height), color="#4A90E2")
        draw = ImageDraw.Draw(image)

        # Draw a simple border
        border_width = 20
        draw.rectangle(
            [border_width, border_width, width - border_width, height - border_width],
            outline="#FFD700",
            width=10,
        )

        # Draw title area
        title_area_height = height // 3
        draw.rectangle(
            [
                border_width + 20,
                border_width + 20,
                width - border_width - 20,
                title_area_height,
            ],
            fill="#FFFFFF",
            outline="#FFD700",
            width=3,
        )

        # Add text (using default font since custom fonts may not be available)
        try:
            # Try to use a larger font if available
            font_large = ImageFont.truetype("arial.ttf", 48)
            font_medium = ImageFont.truetype("arial.ttf", 32)
            font_small = ImageFont.truetype("arial.ttf", 24)
        except:
            # Fallback to default font
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Draw title text
        title = f"{child_name}'s"
        subtitle = "Coloring Book" if template_type == "coloring_book" else "Story Book"

        # Center the text
        text_y = border_width + 60
        draw.text((width // 2, text_y), title, fill="#4A90E2", font=font_medium, anchor="mt")
        draw.text((width // 2, text_y + 50), subtitle, fill="#4A90E2", font=font_large, anchor="mt")

        # Draw a simple illustration (stars and shapes)
        for i in range(10):
            x = 100 + (i % 3) * 200
            y = title_area_height + 100 + (i // 3) * 150
            # Draw stars
            draw.ellipse([x - 30, y - 30, x + 30, y + 30], fill="#FFD700", outline="#FFA500", width=2)

        # Add "Mock Book" watermark
        draw.text(
            (width // 2, height - 50),
            "MOCK PREVIEW",
            fill="#CCCCCC",
            font=font_small,
            anchor="mt",
        )

        # Convert to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG", optimize=True)
        return img_byte_arr.getvalue()

    @staticmethod
    def generate_mock_coloring_page(
        page_number: int,
        theme: str = "animals",
        width: int = 800,
        height: int = 1000,
    ) -> bytes:
        """Generate a mock coloring page (line art)"""
        # Create white background
        image = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(image)

        # Draw simple shapes/outlines for coloring
        # Draw a border
        draw.rectangle([20, 20, width - 20, height - 20], outline="black", width=3)

        # Draw some geometric shapes to represent coloring areas
        shapes = [
            # Circle
            (150, 150, 350, 350),
            # Another circle
            (450, 150, 650, 350),
            # Large shape at bottom
            (150, 450, 650, 850),
        ]

        for shape in shapes:
            draw.ellipse(shape, outline="black", width=4)
            # Add some internal details
            x1, y1, x2, y2 = shape
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            radius = min(x2 - x1, y2 - y1) // 4
            draw.ellipse(
                [
                    center_x - radius,
                    center_y - radius,
                    center_x + radius,
                    center_y + radius,
                ],
                outline="black",
                width=2,
            )

        # Add page number
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()

        draw.text(
            (width // 2, height - 40),
            f"Page {page_number}",
            fill="black",
            font=font,
            anchor="mt",
        )

        # Convert to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG", optimize=True)
        return img_byte_arr.getvalue()

    @staticmethod
    def generate_mock_pdf(
        child_name: str,
        template_type: str,
        num_pages: int = 10,
    ) -> bytes:
        """Generate a mock PDF book"""
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Cover page
        pdf.setFillColorRGB(0.29, 0.56, 0.89)  # Blue background
        pdf.rect(0, 0, width, height, fill=True)

        pdf.setFillColorRGB(1, 1, 1)  # White text
        pdf.setFont("Helvetica-Bold", 36)
        pdf.drawCentredString(width / 2, height - 2 * inch, f"{child_name}'s Book")

        pdf.setFont("Helvetica", 24)
        book_type = "Coloring Book" if template_type == "coloring_book" else "Story Book"
        pdf.drawCentredString(width / 2, height - 3 * inch, book_type)

        pdf.setFont("Helvetica", 12)
        pdf.drawCentredString(width / 2, 1 * inch, "MOCK PREVIEW - Generated by PandaTales")
        pdf.showPage()

        # Content pages
        for page_num in range(1, num_pages + 1):
            # Page background
            pdf.setFillColorRGB(1, 1, 1)
            pdf.rect(0, 0, width, height, fill=True)

            # Page border
            pdf.setStrokeColorRGB(0, 0, 0)
            pdf.setLineWidth(2)
            pdf.rect(0.5 * inch, 0.5 * inch, width - inch, height - inch)

            # Page title
            pdf.setFillColorRGB(0, 0, 0)
            pdf.setFont("Helvetica-Bold", 18)
            pdf.drawCentredString(width / 2, height - 1.5 * inch, f"Page {page_num}")

            # Mock content (placeholders)
            pdf.setFont("Helvetica", 12)
            if template_type == "coloring_book":
                pdf.drawCentredString(
                    width / 2,
                    height / 2,
                    "[Coloring page illustration would appear here]",
                )
            else:
                # Story content
                y_position = height - 2.5 * inch
                lines = [
                    "Once upon a time, in a magical land,",
                    f"{child_name} went on an amazing adventure.",
                    "This is a mock story page.",
                    "The actual content would be generated by AI.",
                ]
                for line in lines:
                    pdf.drawString(inch, y_position, line)
                    y_position -= 0.3 * inch

            # Page number
            pdf.setFont("Helvetica", 10)
            pdf.drawCentredString(width / 2, 0.5 * inch, str(page_num))

            pdf.showPage()

        # Save PDF
        pdf.save()
        return buffer.getvalue()


class MockGenerationWorker:
    """
    Mock worker that simulates the book generation process.
    In production, this would be replaced with actual AI generation.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = GeneratedBookRepository(db)
        self.storage_service = StorageService()
        self.content_generator = MockContentGenerator()

    async def process_generation(self, generation_id: UUID) -> None:
        """
        Main generation process - simulates AI generation with realistic timing.
        This is the function that will be replaced with actual AI calls.
        """
        try:
            logger.info("starting_mock_generation", generation_id=str(generation_id))

            # Get the generation record
            book = await self.repository.get_by_id_direct(generation_id)
            if not book:
                logger.error("generation_not_found", generation_id=str(generation_id))
                return

            # Update status to processing
            await self._update_status(
                generation_id,
                status="processing",
                progress=0,
                current_step="Initializing",
            )

            # Step 1: Process photos (10%)
            await self._update_step(generation_id, "photo_processing", "in_progress", 5)
            await asyncio.sleep(2)  # Simulate processing time
            await self._update_step(generation_id, "photo_processing", "completed", 10)

            # Step 2: Content generation (varies by type)
            if book.generation_type == "photo_to_coloring":
                await self._process_photo_to_coloring(generation_id, book)
            elif book.generation_type == "theme_based":
                await self._process_theme_based(generation_id, book)
            else:
                await self._process_standard_generation(generation_id, book)

            # Mark as completed
            completed_at = datetime.utcnow()
            await self.repository.update_fields(
                generation_id,
                status="completed",
                progress=100,
                current_step="Completed",
                completed_at=completed_at,
            )
            await self.db.commit()

            logger.info("mock_generation_completed", generation_id=str(generation_id))

        except Exception as e:
            logger.error(
                "mock_generation_failed",
                generation_id=str(generation_id),
                error=str(e),
                exc_info=True,
            )
            await self._mark_as_failed(generation_id, str(e))

    async def _process_photo_to_coloring(self, generation_id: UUID, book: Any) -> None:
        """Process photo-to-coloring generation"""
        # Step: Line extraction
        await self._update_step(generation_id, "line_extraction", "in_progress", 20)
        await asyncio.sleep(2)
        await self._update_step(generation_id, "line_extraction", "completed", 40)

        # Step: Edge detection
        await self._update_step(generation_id, "edge_detection", "in_progress", 50)
        await asyncio.sleep(2)
        await self._update_step(generation_id, "edge_detection", "completed", 70)

        # Step: Create coloring pages
        await self._update_step(generation_id, "coloring_page_creation", "in_progress", 75)
        num_pages = len(book.photos)  # One page per photo
        preview_pages = await self._generate_coloring_preview_pages(
            generation_id, book, num_pages
        )
        await self._update_step(generation_id, "coloring_page_creation", "completed", 90)

        # Generate final PDF
        await self._generate_final_pdf(generation_id, book, preview_pages)

    async def _process_theme_based(self, generation_id: UUID, book: Any) -> None:
        """Process theme-based generation"""
        # Step: Theme extraction
        await self._update_step(generation_id, "theme_extraction", "in_progress", 20)
        await asyncio.sleep(2)
        await self._update_step(generation_id, "theme_extraction", "completed", 35)

        # Step: Content generation
        await self._update_step(generation_id, "content_generation", "in_progress", 40)
        await asyncio.sleep(3)
        await self._update_step(generation_id, "content_generation", "completed", 65)

        # Step: Create coloring pages
        await self._update_step(generation_id, "coloring_page_creation", "in_progress", 70)
        num_pages = book.total_pages or 10
        preview_pages = await self._generate_coloring_preview_pages(
            generation_id, book, num_pages, book.selected_theme_name or "general"
        )
        await self._update_step(generation_id, "coloring_page_creation", "completed", 90)

        # Generate final PDF
        await self._generate_final_pdf(generation_id, book, preview_pages)

    async def _process_standard_generation(self, generation_id: UUID, book: Any) -> None:
        """Process standard template-based generation"""
        # Step: Story generation
        await self._update_step(generation_id, "story_generation", "in_progress", 20)
        await asyncio.sleep(3)
        await self._update_step(generation_id, "story_generation", "completed", 45)

        # Step: Image generation
        await self._update_step(generation_id, "image_generation", "in_progress", 50)
        await asyncio.sleep(3)
        num_pages = 10  # Default page count
        preview_pages = await self._generate_story_preview_pages(generation_id, book, num_pages)
        await self._update_step(generation_id, "image_generation", "completed", 80)

        # Step: PDF generation
        await self._update_step(generation_id, "pdf_generation", "in_progress", 85)
        await self._generate_final_pdf(generation_id, book, preview_pages)
        await self._update_step(generation_id, "pdf_generation", "completed", 95)

    async def _generate_coloring_preview_pages(
        self, generation_id: UUID, book: Any, num_pages: int, theme: str = "general"
    ) -> list[dict[str, Any]]:
        """Generate mock coloring page previews and upload to MinIO"""
        preview_pages = []

        for page_num in range(1, min(num_pages, 5) + 1):  # Generate up to 5 preview pages
            # Generate mock coloring page
            page_image_bytes = self.content_generator.generate_mock_coloring_page(
                page_number=page_num, theme=theme
            )

            # Upload to MinIO
            file_obj = io.BytesIO(page_image_bytes)
            file_obj.name = f"page_{page_num}.png"
            object_name = await self.storage_service.upload_file(
                file=file_obj,
                filename=f"page_{page_num}.png",
                prefix=f"generated/{generation_id}/preview",
                content_type="image/png",
            )

            page_url = await self.storage_service.get_presigned_url(object_name, expires_in=3600 * 24 * 7)

            preview_pages.append(
                {
                    "page_number": page_num,
                    "page_url": page_url,
                    "page_object_name": object_name,
                    "thumbnail_url": page_url,  # In production, generate actual thumbnail
                }
            )

        # Update database with preview pages
        await self.repository.update_fields(generation_id, preview_pages=preview_pages, total_pages=num_pages)
        await self.db.commit()

        return preview_pages

    async def _generate_story_preview_pages(
        self, generation_id: UUID, book: Any, num_pages: int
    ) -> list[dict[str, Any]]:
        """Generate mock story page previews"""
        preview_pages = []

        for page_num in range(1, min(num_pages, 5) + 1):
            # Generate mock story page (similar to coloring but with text)
            page_image_bytes = self.content_generator.generate_mock_coloring_page(
                page_number=page_num, theme="story"
            )

            # Upload to MinIO
            file_obj = io.BytesIO(page_image_bytes)
            file_obj.name = f"page_{page_num}.png"
            object_name = await self.storage_service.upload_file(
                file=file_obj,
                filename=f"page_{page_num}.png",
                prefix=f"generated/{generation_id}/preview",
                content_type="image/png",
            )

            page_url = await self.storage_service.get_presigned_url(object_name, expires_in=3600 * 24 * 7)

            preview_pages.append(
                {
                    "page_number": page_num,
                    "page_url": page_url,
                    "page_object_name": object_name,
                    "thumbnail_url": page_url,
                    "page_text": f"This is page {page_num} of {book.child_name}'s story...",
                }
            )

        # Update database with preview pages
        await self.repository.update_fields(generation_id, preview_pages=preview_pages, total_pages=num_pages)
        await self.db.commit()

        return preview_pages

    async def _generate_final_pdf(
        self, generation_id: UUID, book: Any, preview_pages: list[dict[str, Any]]
    ) -> None:
        """Generate final PDF and cover image"""
        # Generate cover image
        cover_image_bytes = self.content_generator.generate_mock_cover_image(
            child_name=book.child_name, template_type=book.template_type
        )

        # Upload cover to MinIO
        cover_file = io.BytesIO(cover_image_bytes)
        cover_file.name = "cover.png"
        cover_object_name = await self.storage_service.upload_file(
            file=cover_file,
            filename="cover.png",
            prefix=f"generated/{generation_id}",
            content_type="image/png",
        )
        cover_url = await self.storage_service.get_presigned_url(
            cover_object_name, expires_in=3600 * 24 * 7
        )

        # Generate PDF
        pdf_bytes = self.content_generator.generate_mock_pdf(
            child_name=book.child_name,
            template_type=book.template_type,
            num_pages=book.total_pages or 10,
        )

        # Upload PDF to MinIO
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_file.name = "book.pdf"
        pdf_object_name = await self.storage_service.upload_file(
            file=pdf_file,
            filename=f"{book.child_name}_book.pdf",
            prefix=f"generated/{generation_id}",
            content_type="application/pdf",
        )

        # Update database with cover and PDF URLs
        await self.repository.update_fields(
            generation_id,
            cover_image_url=cover_url,
            # Store object names for future reference
            generation_steps={
                **(book.generation_steps or {}),
                "cover_object_name": cover_object_name,
                "pdf_object_name": pdf_object_name,
            },
        )
        await self.db.commit()

    async def _update_status(
        self,
        generation_id: UUID,
        status: str,
        progress: int,
        current_step: str,
    ) -> None:
        """Update generation status"""
        await self.repository.update_fields(
            generation_id,
            status=status,
            progress=progress,
            current_step=current_step,
        )
        await self.db.commit()
        logger.info(
            "generation_status_updated",
            generation_id=str(generation_id),
            status=status,
            progress=progress,
            step=current_step,
        )

    async def _update_step(
        self,
        generation_id: UUID,
        step_name: str,
        step_status: str,
        progress: int,
    ) -> None:
        """Update a specific generation step"""
        book = await self.repository.get_by_id_direct(generation_id)
        if book:
            steps = book.generation_steps or {}
            steps[step_name] = step_status

            await self.repository.update_fields(
                generation_id,
                generation_steps=steps,
                progress=progress,
                current_step=step_name.replace("_", " ").title(),
            )
            await self.db.commit()

    async def _mark_as_failed(self, generation_id: UUID, error: str) -> None:
        """Mark generation as failed"""
        await self.repository.update_fields(
            generation_id,
            status="failed",
            error_code="GENERATION_ERROR",
            error_message=error,
            failed_at=datetime.utcnow(),
        )
        await self.db.commit()


async def start_mock_generation(generation_id: UUID, db: AsyncSession) -> None:
    """
    Start a mock generation process in the background.
    This function should be called after a generation is queued.
    
    In production, this would be replaced with:
    - Celery task queue
    - AWS Lambda
    - Azure Functions
    - Or other async job processing system
    """
    worker = MockGenerationWorker(db)
    
    # Run the generation in the background
    # For now, we'll create a task but in production you'd use proper job queue
    asyncio.create_task(worker.process_generation(generation_id))
    
    logger.info("mock_generation_task_created", generation_id=str(generation_id))


# Export for easy importing
__all__ = ["MockGenerationWorker", "MockContentGenerator", "start_mock_generation"]
