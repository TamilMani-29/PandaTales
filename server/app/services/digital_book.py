"""Service layer for digital book catalog operations."""

import asyncio
import smtplib
from datetime import timedelta
from decimal import Decimal
from email.message import EmailMessage
from pathlib import Path

from slugify import slugify
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import BadRequestException, NotFoundException, ServiceUnavailableException, get_logger
from app.core.config import settings
from app.models.book import Book
from app.models.genre import Genre
from app.schemas.digital_book import DigitalBookCreateRequest
from app.services.storage import StorageService

logger = get_logger(__name__)


class DigitalBookService:
    """Business logic for create/list/retrieve and email of digital books."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = StorageService()

    async def create_book(self, data: DigitalBookCreateRequest, cover_image, book_file) -> Book:
        """Create digital book, upload files to MinIO, and persist object paths."""
        if not cover_image.content_type or not cover_image.content_type.startswith("image/"):
            raise BadRequestException("cover_image must be an image file")

        book_ext = Path(book_file.filename or "").suffix.lower()
        if book_ext != ".pdf":
            raise BadRequestException("book_file must be a PDF")

        genre = await self._get_or_create_genre(data.genre)

        book = Book(
            book_name=data.book_name,
            description=data.description,
            total_pages=data.total_pages,
            book_type=data.book_type,
            theme=data.theme,
            style=data.style,
            age_group=data.age_group,
            language=data.language,
            genre_id=genre.id,
            price=float(data.price) if isinstance(data.price, Decimal) else data.price,
        )

        uploaded_objects: list[str] = []
        try:
            self.db.add(book)
            await self.db.flush()

            cover_ext = Path(cover_image.filename or "").suffix.lower() or ".jpg"
            slug = slugify(data.book_name) or f"book-{book.id}"

            cover_object_name = f"digital-books/cover_images/{slug}-{book.id}{cover_ext}"
            book_object_name = f"digital-books/books/{slug}-{book.id}.pdf"

            await self.storage.upload_file(
                file=cover_image,
                object_name=cover_object_name,
                content_type=cover_image.content_type,
                max_size_mb=10,
            )
            uploaded_objects.append(cover_object_name)

            await self.storage.upload_file(
                file=book_file,
                object_name=book_object_name,
                content_type="application/pdf",
                max_size_mb=100,
            )
            uploaded_objects.append(book_object_name)

            book.cover_image_url = cover_object_name
            book.book_url = book_object_name

            await self.db.commit()
            await self.db.refresh(book)
            return book
        except Exception:
            await self.db.rollback()

            for object_name in uploaded_objects:
                try:
                    await self.storage.delete_file(object_name)
                except Exception:
                    logger.warning("digital_book_cleanup_failed", object_name=object_name)

            raise

    async def list_books(
        self,
        *,
        search: str | None = None,
        book_type=None,
        style=None,
        age_group=None,
        language=None,
        genre: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        limit: int = 60,
        offset: int = 0,
    ) -> list[dict]:
        """Return filtered books without PDF URL and with presigned cover URL."""
        query = select(Book, Genre.name).outerjoin(Genre, Book.genre_id == Genre.id)

        if search:
            keyword = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Book.book_name.ilike(keyword),
                    Book.description.ilike(keyword),
                    Genre.name.ilike(keyword),
                )
            )

        if book_type is not None:
            query = query.where(Book.book_type == book_type)
        if style is not None:
            query = query.where(Book.style == style)
        if age_group is not None:
            query = query.where(Book.age_group == age_group)
        if language is not None:
            query = query.where(Book.language == language)
        if genre:
            query = query.where(func.lower(Genre.name) == genre.strip().lower())
        if min_price is not None:
            query = query.where(Book.price >= min_price)
        if max_price is not None:
            query = query.where(Book.price <= max_price)

        query = query.order_by(Book.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        rows = result.all()

        items: list[dict] = []
        for book, genre_name in rows:
            items.append(await self._to_response_dict(book, genre_name=genre_name, include_pdf_url=False))
        return items

    async def get_book(self, book_id: int) -> dict:
        """Return one book without PDF URL and with presigned cover URL."""
        query = select(Book, Genre.name).outerjoin(Genre, Book.genre_id == Genre.id).where(Book.id == book_id)
        result = await self.db.execute(query)
        row = result.first()
        if not row:
            raise NotFoundException("Book not found")

        book, genre_name = row
        return await self._to_response_dict(book, genre_name=genre_name, include_pdf_url=False)

    async def get_filter_options(self) -> dict:
        """Return filter options sourced from constants and existing catalog data."""
        genres_result = await self.db.execute(select(Genre.name).order_by(Genre.name.asc()))
        genres = [name for name in genres_result.scalars().all() if name]

        style_result = await self.db.execute(select(Book.style).where(Book.style.is_not(None)).distinct())
        styles = sorted({item.value for item in style_result.scalars().all() if item is not None})

        return {
            "book_types": ["story", "coloring"],
            "styles": styles or ["animation", "illustration"],
            "age_groups": ["5-9", "10-14"],
            "languages": ["english"],
            "genres": genres,
        }

    async def send_pdf_to_email(self, book_id: int, recipient_email: str) -> None:
        """Download book PDF from MinIO and email it to the recipient."""
        book = await self.db.get(Book, book_id)
        if not book:
            raise NotFoundException("Book not found")
        if not book.book_url:
            raise BadRequestException("Book PDF URL is missing")

        if not settings.SMTP_HOST or not settings.SMTP_PORT:
            raise ServiceUnavailableException("SMTP is not configured")
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            raise ServiceUnavailableException("SMTP credentials are missing")

        pdf_bytes = await self.storage.download_file(book.book_url)

        message = EmailMessage()
        message["Subject"] = f"Your PandaTales book: {book.book_name}"
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = recipient_email
        message.set_content(
            "Hi,\n\n"
            "Please find your requested PandaTales digital book attached as a PDF.\n\n"
            "Thank you for using PandaTales."
        )

        attachment_name = f"{slugify(book.book_name) or 'book'}-{book.id}.pdf"
        message.add_attachment(
            pdf_bytes,
            maintype="application",
            subtype="pdf",
            filename=attachment_name,
        )

        await asyncio.to_thread(self._send_email_sync, message)

    async def _get_or_create_genre(self, genre_name: str) -> Genre:
        normalized = genre_name.strip().lower()
        if not normalized:
            raise BadRequestException("genre is required")

        result = await self.db.execute(select(Genre).where(Genre.name == normalized))
        genre = result.scalar_one_or_none()
        if genre:
            return genre

        genre = Genre(name=normalized)
        self.db.add(genre)
        await self.db.flush()
        return genre

    async def _to_response_dict(self, book: Book, genre_name: str | None, include_pdf_url: bool) -> dict:
        cover_presigned_url = None
        if book.cover_image_url:
            try:
                cover_presigned_url = await self.storage.get_file_url(
                    book.cover_image_url,
                    expires=timedelta(hours=6),
                )
            except Exception:
                logger.warning(
                    "digital_book_cover_presign_failed",
                    book_id=book.id,
                    cover_image_url=book.cover_image_url,
                )

        return {
            "id": book.id,
            "book_name": book.book_name,
            "description": book.description,
            "cover_image_url": book.cover_image_url,
            "cover_image_presigned_url": cover_presigned_url,
            "book_url": book.book_url if include_pdf_url else None,
            "total_pages": book.total_pages,
            "book_type": book.book_type,
            "theme": book.theme,
            "style": book.style,
            "age_group": book.age_group,
            "language": book.language,
            "genre_id": book.genre_id,
            "genre_name": genre_name,
            "price": float(book.price) if book.price is not None else None,
            "rating": book.rating,
            "total_ratings": book.total_ratings,
            "download_count": book.download_count,
            "created_at": book.created_at,
            "updated_at": book.updated_at,
        }

    def _send_email_sync(self, message: EmailMessage) -> None:
        """Blocking SMTP send wrapped by asyncio.to_thread in async call sites."""
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(message)
        except smtplib.SMTPAuthenticationError as exc:
            logger.error("digital_book_email_auth_failed", error=str(exc), exc_info=True)
            raise BadRequestException(
                "SMTP authentication failed. For Gmail, enable 2-Step Verification and use an App Password."
            )
        except Exception as exc:
            logger.error("digital_book_email_send_failed", error=str(exc), exc_info=True)
            raise ServiceUnavailableException("Failed to send email with PDF attachment")
