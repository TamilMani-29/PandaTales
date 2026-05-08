"""Service layer for digital book catalog operations."""

import asyncio
import hashlib
import hmac
import io
import smtplib
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from email.message import EmailMessage
from pathlib import Path
from uuid import uuid4

import razorpay
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from slugify import slugify
from sqlalchemy import func, or_, select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import BadRequestException, NotFoundException, ServiceUnavailableException, get_logger
from app.core.config import settings
from app.models.book import Book
from app.models.book_attribute_option import BookAttributeOption
from app.models.book_category import BookCategory
from app.models.digital_book_order import DigitalBookOrder
from app.models.genre import Genre
from app.models.user import User
from app.schemas.digital_book import (
    BookCategoryCreateRequest,
    DigitalBookCreateRequest,
    DigitalBookPaymentCreateRequest,
    DigitalBookPurchaseRequest,
    DigitalBookUpdateRequest,
)
from app.services.storage import StorageService

logger = get_logger(__name__)


GST_RATE_DIGITAL_PERCENT = 18
SUPPORTED_ATTRIBUTE_OPTION_TYPES = {"book_type", "theme", "language", "genre"}
DEFAULT_ATTRIBUTE_OPTIONS: dict[str, list[str]] = {
    "book_type": ["story", "coloring", "activity", "workbook", "comic", "poetry"],
    "theme": [
        "human", "animal", "fantasy", "nature", "space", "ocean",
        "jungle", "mythology", "sports", "technology",
    ],
    "language": [
        "english", "hindi", "tamil", "telugu", "kannada",
        "malayalam", "marathi", "bengali", "gujarati", "punjabi",
    ],
}
DEFAULT_GENRES: list[str] = [
    "fantasy", "adventure", "mystery", "humor", "educational",
    "fairy tale", "mythology", "science fiction", "realistic fiction",
    "poetry", "nature", "history",
]


class DigitalBookService:
    """Business logic for create/list/retrieve and email of digital books."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = StorageService()
        self._key_id = settings.RAZORPAY_KEY_ID
        self._key_secret = settings.RAZORPAY_KEY_SECRET
        self._payment_client = (
            razorpay.Client(auth=(self._key_id, self._key_secret))
            if self._key_id and self._key_secret
            else None
        )

    async def create_book(
        self,
        data: DigitalBookCreateRequest,
        cover_image,
        front_image,
        back_image,
        book_file,
    ) -> Book:
        """Create digital book, upload files to MinIO, and persist object paths."""
        if not cover_image.content_type or not cover_image.content_type.startswith("image/"):
            raise BadRequestException("cover_image must be an image file")

        if front_image is not None and (
            not front_image.content_type or not front_image.content_type.startswith("image/")
        ):
            raise BadRequestException("front_image must be an image file")

        if back_image is not None and (
            not back_image.content_type or not back_image.content_type.startswith("image/")
        ):
            raise BadRequestException("back_image must be an image file")

        if book_file is not None:
            book_ext = Path(book_file.filename or "").suffix.lower()
            if book_ext != ".pdf":
                raise BadRequestException("book_file must be a PDF")
        elif not data.is_personalized:
            raise BadRequestException("book_file (PDF) is required for non-personalized books")

        genre = await self._get_or_create_genre(data.genre)
        normalized_book_tag = self._merge_tags_to_storage(data.book_tags, data.book_tag)
        normalized_category_id = await self._normalize_and_validate_category_id(data.category_id)
        if normalized_category_id is None and not data.is_personalized:
            raise BadRequestException(
                "category_id is required and must reference an existing category"
            )

        book_type_id = await self._normalize_and_validate_attribute_option("book_type", data.book_type)
        theme_id = await self._normalize_and_validate_attribute_option("theme", data.theme)
        language_id = await self._normalize_and_validate_attribute_option("language", data.language)

        book = Book(
            book_name=data.book_name,
            description=data.description,
            book_tag=normalized_book_tag,
            category_id=normalized_category_id,
            emoji=(data.emoji.strip() if data.emoji else None),
            total_pages=data.total_pages,
            book_type_id=book_type_id,
            theme_id=theme_id,
            language_id=language_id,
            genre_id=genre.id,
            price=float(data.price) if isinstance(data.price, Decimal) else data.price,
            rating=float(data.rating) if data.rating is not None else 0.0,
            total_ratings=data.total_ratings or 0,
            download_count=data.download_count or 0,
            is_bestseller=data.is_bestseller,
            is_personalized=data.is_personalized,
        )

        uploaded_objects: list[str] = []
        try:
            self.db.add(book)
            await self.db.flush()

            cover_ext = Path(cover_image.filename or "").suffix.lower() or ".jpg"
            slug = slugify(data.book_name) or f"book-{book.id}"

            cover_object_name = f"digital-books/cover_images/{slug}-{book.id}{cover_ext}"
            front_ext = Path(front_image.filename or "").suffix.lower() if front_image else cover_ext
            back_ext = Path(back_image.filename or "").suffix.lower() if back_image else cover_ext
            front_object_name = f"digital-books/front_images/{slug}-{book.id}{front_ext or '.jpg'}"
            back_object_name = f"digital-books/back_images/{slug}-{book.id}{back_ext or '.jpg'}"
            book_object_name = f"digital-books/books/{slug}-{book.id}.pdf"

            await self.storage.upload_file(
                file=cover_image,
                object_name=cover_object_name,
                content_type=cover_image.content_type,
                max_size_mb=10,
            )
            uploaded_objects.append(cover_object_name)

            if front_image:
                await self.storage.upload_file(
                    file=front_image,
                    object_name=front_object_name,
                    content_type=front_image.content_type,
                    max_size_mb=10,
                )
                uploaded_objects.append(front_object_name)

            if back_image:
                await self.storage.upload_file(
                    file=back_image,
                    object_name=back_object_name,
                    content_type=back_image.content_type,
                    max_size_mb=10,
                )
                uploaded_objects.append(back_object_name)

            if book_file is not None:
                await self.storage.upload_file(
                    file=book_file,
                    object_name=book_object_name,
                    content_type="application/pdf",
                    max_size_mb=100,
                )
                uploaded_objects.append(book_object_name)
                book.book_url = book_object_name

            book.cover_image_url = cover_object_name
            book.front_image_url = front_object_name if front_image else cover_object_name
            book.back_image_url = back_object_name if back_image else cover_object_name

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
        language=None,
        genre: str | None = None,
        category_id: int | None = None,
        is_bestseller: bool | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        limit: int = 60,
        offset: int = 0,
    ) -> list[dict]:
        """Return filtered books without PDF URL and with presigned cover URL."""
        BookTypeOpt = aliased(BookAttributeOption)
        ThemeOpt = aliased(BookAttributeOption)
        LanguageOpt = aliased(BookAttributeOption)
        query = (
            select(
                Book,
                Genre.name,
                BookCategory.name,
                BookCategory.personalized_tag,
                BookCategory.description,
                BookTypeOpt.value,
                ThemeOpt.value,
                LanguageOpt.value,
            )
            .outerjoin(Genre, Book.genre_id == Genre.id)
            .outerjoin(BookCategory, Book.category_id == BookCategory.category_id)
            .outerjoin(BookTypeOpt, Book.book_type_id == BookTypeOpt.id)
            .outerjoin(ThemeOpt, Book.theme_id == ThemeOpt.id)
            .outerjoin(LanguageOpt, Book.language_id == LanguageOpt.id)
        )

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
            query = query.where(
                Book.book_type_id.in_(
                    select(BookAttributeOption.id).where(
                        BookAttributeOption.option_type == "book_type",
                        BookAttributeOption.value == book_type.strip().lower(),
                    )
                )
            )
        if language is not None:
            query = query.where(
                Book.language_id.in_(
                    select(BookAttributeOption.id).where(
                        BookAttributeOption.option_type == "language",
                        BookAttributeOption.value == language.strip().lower(),
                    )
                )
            )
        if genre:
            query = query.where(func.lower(Genre.name) == genre.strip().lower())
        if category_id is not None:
            query = query.where(Book.category_id == category_id)
        if is_bestseller is not None:
            query = query.where(Book.is_bestseller == is_bestseller)
        if min_price is not None:
            query = query.where(Book.price >= min_price)
        if max_price is not None:
            query = query.where(Book.price <= max_price)

        query = query.order_by(Book.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        rows = result.all()

        items: list[dict] = []
        for book, genre_name, category_name, category_tag, category_description, book_type_val, theme_val, language_val in rows:
            items.append(
                await self._to_response_dict(
                    book,
                    genre_name=genre_name,
                    include_pdf_url=False,
                    category_name=category_name,
                    category_tag=category_tag,
                    category_description=category_description,
                    book_type=book_type_val,
                    theme=theme_val,
                    language=language_val,
                )
            )
        return items

    async def get_book(self, book_id: int) -> dict:
        """Return one book without PDF URL and with presigned cover URL."""
        BookTypeOpt = aliased(BookAttributeOption)
        ThemeOpt = aliased(BookAttributeOption)
        LanguageOpt = aliased(BookAttributeOption)
        query = (
            select(
                Book,
                Genre.name,
                BookCategory.name,
                BookCategory.personalized_tag,
                BookCategory.description,
                BookTypeOpt.value,
                ThemeOpt.value,
                LanguageOpt.value,
            )
            .outerjoin(Genre, Book.genre_id == Genre.id)
            .outerjoin(BookCategory, Book.category_id == BookCategory.category_id)
            .outerjoin(BookTypeOpt, Book.book_type_id == BookTypeOpt.id)
            .outerjoin(ThemeOpt, Book.theme_id == ThemeOpt.id)
            .outerjoin(LanguageOpt, Book.language_id == LanguageOpt.id)
            .where(Book.id == book_id)
        )
        result = await self.db.execute(query)
        row = result.first()
        if not row:
            raise NotFoundException("Book not found")

        book, genre_name, category_name, category_tag, category_description, book_type_val, theme_val, language_val = row
        return await self._to_response_dict(
            book,
            genre_name=genre_name,
            include_pdf_url=False,
            category_name=category_name,
            category_tag=category_tag,
            category_description=category_description,
            book_type=book_type_val,
            theme=theme_val,
            language=language_val,
        )

    async def list_categories(self, *, active_only: bool = True) -> list[dict]:
        """Return digital book categories ordered by category_id."""
        query = select(BookCategory)
        if active_only:
            query = query.where(BookCategory.is_active.is_(True))
        query = query.order_by(BookCategory.category_id.asc())

        result = await self.db.execute(query)
        rows = result.scalars().all()
        return [
            {
                "id": row.id,
                "category_id": row.category_id,
                "name": row.name,
                "tags": self._split_tags(row.personalized_tag),
                "personalized_tag": row.personalized_tag,
                "description": row.description,
                "emoji": row.emoji,
                "color": row.color,
                "grad": row.grad,
                "personalized": row.personalized,
                "is_active": row.is_active,
                "label": row.label,
            }
            for row in rows
        ]

    async def create_or_update_category(self, payload: BookCategoryCreateRequest) -> dict:
        """Create category metadata or update existing by category_id.
        """
        requested_id = payload.category_id
        if requested_id is None:
            max_id_result = await self.db.execute(select(func.max(BookCategory.category_id)))
            current_max = max_id_result.scalar_one_or_none() or 0
            normalized_id = int(current_max) + 1
        else:
            if requested_id <= 0:
                raise BadRequestException("category_id must be greater than 0")
            normalized_id = requested_id

        result = await self.db.execute(
            select(BookCategory).where(BookCategory.category_id == normalized_id)
        )
        row = result.scalar_one_or_none()

        if row is None:
            normalized_category_tag = self._merge_tags_to_storage(payload.tags, None)
            row = BookCategory(
                category_id=normalized_id,
                name=payload.name.strip(),
                personalized_tag=normalized_category_tag,
                label=payload.label,
                description=payload.description,
                emoji=payload.emoji,
                color=payload.color,
                grad=payload.grad,
                personalized=payload.personalized,
                is_active=payload.is_active,
            )
            self.db.add(row)
        else:
            row.name = payload.name.strip()
            row.personalized_tag = self._merge_tags_to_storage(payload.tags, None)
            row.label = payload.label
            row.description = payload.description
            row.emoji = payload.emoji
            row.color = payload.color
            row.grad = payload.grad
            row.personalized = payload.personalized
            row.is_active = payload.is_active

        await self.db.commit()
        await self.db.refresh(row)

        return {
            "id": row.id,
            "category_id": row.category_id,
            "name": row.name,
            "tags": self._split_tags(row.personalized_tag),
            "personalized_tag": row.personalized_tag,
            "label": row.label,
            "description": row.description,
            "emoji": row.emoji,
            "color": row.color,
            "grad": row.grad,
            "personalized": row.personalized,
            "is_active": row.is_active,
        }

    async def add_book_category(self, book_id: int, category_id: int) -> dict:
        """Assign or update category for a book."""
        book = await self.db.get(Book, book_id)
        if not book:
            raise NotFoundException("Book not found")

        validated = await self._normalize_and_validate_category_id(category_id)
        if validated is None:
            raise BadRequestException("category_id is required")

        book.category_id = validated
        await self.db.commit()

        return {
            "book_id": book.id,
            "category_id": validated,
        }

    async def update_book(self, book_id: int, data: DigitalBookUpdateRequest) -> dict:
        """Partially update digital book metadata (no file re-upload)."""
        book = await self.db.get(Book, book_id)
        if not book:
            raise NotFoundException("Book not found")

        if data.book_name is not None:
            book.book_name = data.book_name
        if data.description is not None:
            book.description = data.description
        if data.book_tags is not None or data.book_tag is not None:
            book.book_tag = self._merge_tags_to_storage(data.book_tags, data.book_tag)
        if data.category_id is not None:
            book.category_id = await self._normalize_and_validate_category_id(data.category_id)
        if data.emoji is not None:
            book.emoji = data.emoji.strip()
        if data.total_pages is not None:
            book.total_pages = data.total_pages
        if data.book_type is not None:
            book.book_type_id = await self._normalize_and_validate_attribute_option("book_type", data.book_type)
        if data.theme is not None:
            book.theme_id = await self._normalize_and_validate_attribute_option("theme", data.theme)
        if data.language is not None:
            book.language_id = await self._normalize_and_validate_attribute_option("language", data.language)
        if data.genre is not None:
            genre = await self._get_or_create_genre(data.genre)
            book.genre_id = genre.id
        if data.price is not None:
            book.price = float(data.price)
        if data.rating is not None:
            book.rating = data.rating
        if data.total_ratings is not None:
            book.total_ratings = data.total_ratings
        if data.download_count is not None:
            book.download_count = data.download_count
        if data.is_bestseller is not None:
            book.is_bestseller = data.is_bestseller
        if data.is_personalized is not None:
            book.is_personalized = data.is_personalized

        await self.db.commit()
        await self.db.refresh(book)

        BookTypeOpt = aliased(BookAttributeOption)
        ThemeOpt = aliased(BookAttributeOption)
        LanguageOpt = aliased(BookAttributeOption)
        query = (
            select(
                Book,
                Genre.name,
                BookCategory.name,
                BookCategory.personalized_tag,
                BookCategory.description,
                BookTypeOpt.value,
                ThemeOpt.value,
                LanguageOpt.value,
            )
            .outerjoin(Genre, Book.genre_id == Genre.id)
            .outerjoin(BookCategory, Book.category_id == BookCategory.category_id)
            .outerjoin(BookTypeOpt, Book.book_type_id == BookTypeOpt.id)
            .outerjoin(ThemeOpt, Book.theme_id == ThemeOpt.id)
            .outerjoin(LanguageOpt, Book.language_id == LanguageOpt.id)
            .where(Book.id == book_id)
        )
        result = await self.db.execute(query)
        row = result.first()
        if row:
            book_row, genre_name, category_name, category_tag, category_description, book_type_val, theme_val, language_val = row
            return await self._to_response_dict(
                book_row,
                genre_name=genre_name,
                include_pdf_url=False,
                category_name=category_name,
                category_tag=category_tag,
                category_description=category_description,
                book_type=book_type_val,
                theme=theme_val,
                language=language_val,
            )

        return await self._to_response_dict(book, genre_name=None, include_pdf_url=False)

    async def delete_book(self, book_id: int) -> dict:
        """Delete a digital book record. MinIO assets are not removed."""
        book = await self.db.get(Book, book_id)
        if not book:
            raise NotFoundException("Book not found")
        await self.db.delete(book)
        await self.db.commit()
        return {"book_id": book_id, "deleted": True}

    async def delete_category(self, category_id: int) -> dict:
        """Delete a book category row by category_id."""
        if category_id <= 0:
            raise BadRequestException("category_id must be greater than 0")
        result = await self.db.execute(
            select(BookCategory).where(BookCategory.category_id == category_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise NotFoundException("Category not found")

        books_result = await self.db.execute(
            select(Book).where(Book.category_id == category_id)
        )
        books_to_delete = books_result.scalars().all()
        deleted_books = 0
        for book in books_to_delete:
            await self.db.delete(book)
            deleted_books += 1

        await self.db.delete(row)
        await self.db.commit()
        return {
            "category_id": category_id,
            "deleted": True,
            "deleted_books_count": deleted_books,
        }

    async def get_filter_options(self) -> dict:
        """Return filter options sourced from constants and existing catalog data."""
        await self._ensure_default_attribute_options()

        genres_result = await self.db.execute(select(Genre.name).order_by(Genre.name.asc()))
        genres = [name for name in genres_result.scalars().all() if name]

        options_result = await self.db.execute(
            select(BookAttributeOption)
            .where(BookAttributeOption.is_active.is_(True))
            .order_by(BookAttributeOption.option_type.asc(), BookAttributeOption.value.asc())
        )
        option_rows = options_result.scalars().all()

        grouped: dict[str, list[str]] = {"book_type": [], "theme": [], "language": []}
        for row in option_rows:
            values = grouped.get(row.option_type)
            if values is not None:
                values.append(row.value)

        return {
            "book_types": grouped["book_type"],
            "themes": grouped["theme"],
            "languages": grouped["language"],
            "genres": genres,
        }

    async def list_attribute_options(self) -> dict[str, list[str]]:
        """Return admin-managed dropdown values for book metadata fields."""
        await self._ensure_default_attribute_options()
        filter_options = await self.get_filter_options()
        return {
            "book_type": filter_options.get("book_types", []),
            "theme": filter_options.get("themes", []),
            "language": filter_options.get("languages", []),
            "genre": filter_options.get("genres", []),
        }

    async def create_attribute_option(self, option_type: str, value: str) -> dict[str, str]:
        normalized_type = self._normalize_option_type(option_type)
        normalized_value = self._normalize_option_value(value)

        if normalized_type == "genre":
            await self._get_or_create_genre(normalized_value)
            await self.db.commit()
            return {"option_type": normalized_type, "value": normalized_value}

        existing = await self.db.execute(
            select(BookAttributeOption).where(
                BookAttributeOption.option_type == normalized_type,
                BookAttributeOption.value == normalized_value,
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            row.is_active = True
        else:
            row = BookAttributeOption(
                option_type=normalized_type,
                value=normalized_value,
                is_active=True,
            )
            self.db.add(row)

        await self.db.commit()
        return {"option_type": normalized_type, "value": normalized_value}

    async def delete_attribute_option(self, option_type: str, value: str) -> dict[str, str | bool]:
        normalized_type = self._normalize_option_type(option_type)
        normalized_value = self._normalize_option_value(value)

        if normalized_type == "genre":
            result = await self.db.execute(select(Genre).where(Genre.name == normalized_value))
            genre = result.scalar_one_or_none()
            if genre is None:
                raise NotFoundException("Genre option not found")

            in_use = await self.db.execute(
                select(func.count(Book.id)).where(Book.genre_id == genre.id)
            )
            if int(in_use.scalar_one() or 0) > 0:
                raise BadRequestException("Cannot delete genre currently used by books")

            await self.db.delete(genre)
            await self.db.commit()
            return {"option_type": normalized_type, "value": normalized_value, "deleted": True}

        in_use_column = {
            "book_type": Book.book_type_id,
            "theme": Book.theme_id,
            "language": Book.language_id,
        }.get(normalized_type)

        if in_use_column is None:
            raise BadRequestException("Unsupported option type")

        result = await self.db.execute(
            select(BookAttributeOption).where(
                BookAttributeOption.option_type == normalized_type,
                BookAttributeOption.value == normalized_value,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise NotFoundException("Attribute option not found")

        in_use = await self.db.execute(
            select(func.count(Book.id)).where(in_use_column == row.id)
        )
        if int(in_use.scalar_one() or 0) > 0:
            raise BadRequestException("Cannot delete option currently used by books")

        await self.db.delete(row)
        await self.db.commit()
        return {"option_type": normalized_type, "value": normalized_value, "deleted": True}

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
        message["Subject"] = "✨ Your book is ready! Download now | Pandora Pages"
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = recipient_email

        recipient_name = self._guess_parent_name(recipient_email)
        message.set_content(
            f"Hi {recipient_name} 👋\n\n"
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

        attachment_name = f"{slugify(book.book_name) or 'book'}-{book.id}.pdf"
        message.add_attachment(
            pdf_bytes,
            maintype="application",
            subtype="pdf",
            filename=attachment_name,
        )

        await asyncio.to_thread(self._send_email_sync, message)

    @staticmethod
    def _guess_parent_name(email: str) -> str:
        local = (email or "").split("@", 1)[0].strip()
        if not local:
            return "there"
        cleaned = local.replace(".", " ").replace("_", " ").replace("-", " ")
        return " ".join(part.capitalize() for part in cleaned.split() if part) or "there"

    async def create_purchase_order(
        self,
        *,
        user: User,
        payload: DigitalBookPurchaseRequest,
    ) -> dict:
        """Backward-compatible purchase flow; now creates payment order first."""
        payment_payload = DigitalBookPaymentCreateRequest(
            book_id=payload.book_id,
            delivery_method=payload.delivery_method,
            delivery_contact=payload.delivery_contact,
        )
        return await self.create_payment_order(user=user, payload=payment_payload)

    async def create_payment_order(
        self,
        *,
        user: User,
        payload: DigitalBookPaymentCreateRequest,
    ) -> dict:
        """Create Razorpay order and persist pending digital payment record."""
        if not self._payment_client:
            raise BadRequestException(
                "Payment gateway is not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in environment."
            )

        book = await self.db.get(Book, payload.book_id)
        if not book:
            raise NotFoundException("Book not found")

        if book.price is None:
            raise BadRequestException("Book price is missing")

        delivery_contact = payload.delivery_contact.strip()
        taxable_amount_paise = int(Decimal(str(book.price)) * 100)
        gst_rate_percent = self._gst_rate_for_digital_book(book)
        gst_amount_paise = self._calculate_gst_amount_paise(
            taxable_amount_paise,
            gst_rate_percent,
        )
        total_amount_paise = taxable_amount_paise + gst_amount_paise

        rz_order = self._payment_client.order.create(
            {
                "amount": total_amount_paise,
                "currency": "INR",
                "payment_capture": 1,
                "notes": {
                    "book_id": str(book.id),
                    "user_id": str(user.id),
                    "delivery_method": payload.delivery_method,
                    "delivery_contact": delivery_contact,
                    "taxable_amount": str(taxable_amount_paise),
                    "gst_rate_percent": str(gst_rate_percent),
                    "gst_amount": str(gst_amount_paise),
                },
            }
        )

        order = DigitalBookOrder(
            user_id=user.id,
            book_id=book.id,
            delivery_method=payload.delivery_method,
            delivery_contact=delivery_contact,
            amount=total_amount_paise,
            currency="INR",
            razorpay_order_id=rz_order["id"],
            payment_status="created",
            status="created",
            delivery_status="pending",
        )
        self.db.add(order)

        await self.db.commit()
        await self.db.refresh(order)

        return {
            "order_id": order.id,
            "user_id": order.user_id,
            "book_id": order.book_id,
            "amount": order.amount,
            "taxable_amount": taxable_amount_paise,
            "gst_rate_percent": gst_rate_percent,
            "gst_amount": gst_amount_paise,
            "total_amount": total_amount_paise,
            "currency": order.currency,
            "key_id": self._key_id,
            "razorpay_order_id": order.razorpay_order_id,
            "payment_status": order.payment_status,
            "delivery_method": order.delivery_method,
            "delivery_contact": order.delivery_contact,
        }

    async def verify_payment(
        self,
        *,
        user: User,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> dict:
        """Verify Razorpay signature and mark digital payment as paid/failed."""
        if not self._key_secret:
            raise BadRequestException("Payment gateway is not configured")

        result = await self.db.execute(
            select(DigitalBookOrder).where(DigitalBookOrder.razorpay_order_id == razorpay_order_id)
        )
        order = result.scalar_one_or_none()
        if not order or order.user_id != user.id:
            raise NotFoundException("Payment order not found")

        if order.payment_status == "paid":
            return await self._payment_history_item(order)

        expected_signature = hmac.new(
            self._key_secret.encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, razorpay_signature):
            order.payment_status = "failed"
            order.status = "failed"
            order.payment_error = "Invalid Razorpay signature"
            await self.db.commit()
            raise BadRequestException("Payment verification failed: invalid signature")

        order.razorpay_payment_id = razorpay_payment_id
        order.razorpay_signature = razorpay_signature
        order.payment_status = "paid"
        order.status = "paid"
        order.payment_error = None
        order.paid_at = datetime.now(timezone.utc)

        book = await self.db.get(Book, order.book_id)
        if book:
            book.download_count = (book.download_count or 0) + 1

        if order.delivery_method == "email":
            await self.send_pdf_to_email(book_id=order.book_id, recipient_email=order.delivery_contact)
            order.delivery_status = "sent"
            order.delivery_sent_at = datetime.now(timezone.utc)
            order.status = "delivered"

        invoice_recipients = [user.email]
        if order.delivery_method == "email":
            delivery_email = order.delivery_contact.strip().lower()
            if delivery_email and delivery_email != user.email.strip().lower():
                invoice_recipients.append(order.delivery_contact)

        try:
            await self.send_invoice_email(
                order=order,
                user=user,
                book=book,
                recipients=invoice_recipients,
            )
        except Exception as exc:
            logger.warning(
                "digital_book_invoice_email_failed",
                order_id=order.id,
                user_id=str(user.id),
                error=str(exc),
            )

        await self.db.commit()
        await self.db.refresh(order)
        return await self._payment_history_item(order)

    async def list_payment_history(self, *, user_id) -> list[dict]:
        """List digital payment history for one user."""
        result = await self.db.execute(
            select(DigitalBookOrder)
            .where(DigitalBookOrder.user_id == user_id)
            .order_by(DigitalBookOrder.created_at.desc())
        )
        rows = result.scalars().all()
        return [await self._payment_history_item(row) for row in rows]

    async def _payment_history_item(self, order: DigitalBookOrder) -> dict:
        book = await self.db.get(Book, order.book_id)
        if book and book.price is not None:
            taxable_amount_paise = int(Decimal(str(book.price)) * 100)
            gst_rate_percent = self._gst_rate_for_digital_book(book)
        else:
            taxable_amount_paise = order.amount
            gst_rate_percent = 0

        gst_amount_paise = max(order.amount - taxable_amount_paise, 0)

        return {
            "order_id": order.id,
            "user_id": order.user_id,
            "book_id": order.book_id,
            "book_name": book.book_name if book else "Unknown",
            "amount": order.amount,
            "taxable_amount": taxable_amount_paise,
            "gst_rate_percent": gst_rate_percent,
            "gst_amount": gst_amount_paise,
            "total_amount": order.amount,
            "currency": order.currency,
            "payment_status": order.payment_status,
            "status": order.status,
            "razorpay_order_id": order.razorpay_order_id,
            "razorpay_payment_id": order.razorpay_payment_id,
            "delivery_method": order.delivery_method,
            "delivery_contact": order.delivery_contact,
            "delivery_status": order.delivery_status,
            "payment_error": order.payment_error,
            "created_at": order.created_at,
            "paid_at": order.paid_at,
            "delivery_sent_at": order.delivery_sent_at,
        }

    async def get_watermarked_preview(self, book_id: int) -> dict[str, str | int]:
        """Build a watermarked preview PDF, upload it, and return a presigned URL."""
        book = await self.db.get(Book, book_id)
        if not book:
            raise NotFoundException("Book not found")
        if not book.book_url:
            raise BadRequestException("Book PDF URL is missing")

        original_pdf = await self.storage.download_file(book.book_url)
        watermarked_pdf = await asyncio.to_thread(
            self._generate_watermarked_pdf_sync,
            original_pdf,
            book.book_name,
        )

        preview_slug = slugify(book.book_name) or f"book-{book.id}"
        preview_object_name = (
            f"digital-books/previews/{preview_slug}-{book.id}-{uuid4().hex[:10]}.pdf"
        )

        await self.storage.upload_file(
            file=io.BytesIO(watermarked_pdf),
            object_name=preview_object_name,
            content_type="application/pdf",
            max_size_mb=120,
        )

        expires = timedelta(hours=1)
        preview_url = await self.storage.get_file_url(preview_object_name, expires=expires)

        return {
            "preview_url": preview_url,
            "expires_in_seconds": int(expires.total_seconds()),
        }

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

    async def _normalize_and_validate_attribute_option(self, option_type: str, value: str) -> int:
        normalized_type = self._normalize_option_type(option_type)
        normalized_value = self._normalize_option_value(value)

        await self._ensure_default_attribute_options()

        result = await self.db.execute(
            select(BookAttributeOption.id).where(
                BookAttributeOption.option_type == normalized_type,
                BookAttributeOption.value == normalized_value,
                BookAttributeOption.is_active.is_(True),
            )
        )
        option_id = result.scalar_one_or_none()
        if option_id is None:
            raise BadRequestException(f"{normalized_type} option is invalid")
        return int(option_id)

    async def _ensure_default_attribute_options(self) -> None:
        changed = False
        for option_type, values in DEFAULT_ATTRIBUTE_OPTIONS.items():
            for value in values:
                normalized_value = self._normalize_option_value(value)
                result = await self.db.execute(
                    select(BookAttributeOption).where(
                        BookAttributeOption.option_type == option_type,
                        BookAttributeOption.value == normalized_value,
                    )
                )
                row = result.scalar_one_or_none()
                if row is None:
                    self.db.add(
                        BookAttributeOption(
                            option_type=option_type,
                            value=normalized_value,
                            is_active=True,
                        )
                    )
                    changed = True
                elif not row.is_active:
                    row.is_active = True
                    changed = True

        # Seed default genres into the genres table
        for genre_name in DEFAULT_GENRES:
            normalized = self._normalize_option_value(genre_name)
            result = await self.db.execute(select(Genre).where(Genre.name == normalized))
            if result.scalar_one_or_none() is None:
                self.db.add(Genre(name=normalized))
                changed = True

        if changed:
            await self.db.commit()

    @staticmethod
    def _normalize_option_type(option_type: str) -> str:
        normalized = (option_type or "").strip().lower()
        if normalized not in SUPPORTED_ATTRIBUTE_OPTION_TYPES:
            raise BadRequestException("Unsupported option type")
        return normalized

    @staticmethod
    def _normalize_option_value(value: str) -> str:
        normalized = (value or "").strip().lower()
        if not normalized:
            raise BadRequestException("Option value is required")
        return normalized

    async def _to_response_dict(
        self,
        book: Book,
        genre_name: str | None,
        include_pdf_url: bool,
        category_name: str | None = None,
        category_tag: str | None = None,
        category_description: str | None = None,
        book_type: str | None = None,
        theme: str | None = None,
        language: str | None = None,
    ) -> dict:
        cover_presigned_url = await self._presign_url(book.cover_image_url, book.id, "cover")
        front_presigned_url = await self._presign_url(book.front_image_url, book.id, "front")
        back_presigned_url = await self._presign_url(book.back_image_url, book.id, "back")

        return {
            "id": book.id,
            "book_name": book.book_name,
            "description": book.description,
            "book_tag": book.book_tag,
            "book_tags": self._split_tags(book.book_tag),
            "category_id": book.category_id,
            "category": book.category_id,
            "category_name": category_name,
            "category_tag": category_tag,
            "category_tags": self._split_tags(category_tag),
            "category_description": category_description,
            "emoji": book.emoji,
            "is_bestseller": book.is_bestseller,
            "is_personalized": book.is_personalized,
            "cover_image_url": book.cover_image_url,
            "cover_image_presigned_url": cover_presigned_url,
            "front_image_url": book.front_image_url,
            "front_image_presigned_url": front_presigned_url,
            "back_image_url": book.back_image_url,
            "back_image_presigned_url": back_presigned_url,
            "book_url": book.book_url if include_pdf_url else None,
            "total_pages": book.total_pages,
            "book_type_id": book.book_type_id,
            "theme_id": book.theme_id,
            "language_id": book.language_id,
            "book_type": book_type,
            "theme": theme,
            "language": language,
            "genre_id": book.genre_id,
            "genre_name": genre_name,
            "price": float(book.price) if book.price is not None else None,
            "rating": book.rating,
            "total_ratings": book.total_ratings,
            "download_count": book.download_count,
            "created_at": book.created_at,
            "updated_at": book.updated_at,
            "title": book.book_name,
            "desc": book.description,
            "pages": book.total_pages,
            "rat": book.rating,
            "rev": book.total_ratings,
        }

    @staticmethod
    def _split_tags(tag_value: str | None) -> list[str]:
        if not tag_value:
            return []
        return [item.strip() for item in tag_value.split(",") if item and item.strip()]

    def _merge_tags_to_storage(self, tags: list[str] | None, fallback_tag: str | None) -> str | None:
        if tags is not None:
            normalized = [item.strip() for item in tags if item and item.strip()]
            return ", ".join(dict.fromkeys(normalized)) or None

        if fallback_tag is None:
            return None

        fallback_items = [item.strip() for item in fallback_tag.split(",") if item and item.strip()]
        return ", ".join(dict.fromkeys(fallback_items)) or None

    async def _normalize_and_validate_category_id(self, category_id: int | None) -> int | None:
        if category_id is None:
            return None

        if category_id <= 0:
            return None

        category_exists = await self.db.execute(
            select(BookCategory.id).where(BookCategory.category_id == category_id)
        )
        if category_exists.scalar_one_or_none() is None:
            raise BadRequestException(
                "Category not found. Create category first using /digital-books/categories"
            )

        return category_id

    async def _presign_url(self, object_name: str | None, book_id: int, image_kind: str) -> str | None:
        if not object_name:
            return None

        try:
            return await self.storage.get_file_url(
                object_name,
                expires=timedelta(hours=6),
                check_exists=False,
            )
        except Exception:
            logger.warning(
                "digital_book_presign_failed",
                book_id=book_id,
                image_kind=image_kind,
                object_name=object_name,
            )
            return None

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

    def _generate_watermarked_pdf_sync(self, pdf_bytes: bytes, watermark_text: str) -> bytes:
        """Apply diagonal text watermark on every page of a PDF."""
        input_stream = io.BytesIO(pdf_bytes)
        reader = PdfReader(input_stream)
        writer = PdfWriter()

        safe_text = (watermark_text or "PandaTales").strip() or "PandaTales"
        watermark_label = f"PandaTales | {safe_text}"

        for page in reader.pages:
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)

            overlay_stream = io.BytesIO()
            overlay_canvas = canvas.Canvas(overlay_stream, pagesize=(width, height))
            overlay_canvas.saveState()

            try:
                overlay_canvas.setFillAlpha(0.35)
            except Exception:
                pass

            overlay_canvas.setFillColor(Color(0.08, 0.08, 0.08, alpha=0.35))
            overlay_canvas.translate(width / 2, height / 2)
            overlay_canvas.rotate(35)

            font_size = max(18, int(min(width, height) / 12))
            overlay_canvas.setFont("Helvetica-Bold", font_size)
            text_width = overlay_canvas.stringWidth(watermark_label, "Helvetica-Bold", font_size)
            overlay_canvas.drawString(-text_width / 2, 0, watermark_label)

            overlay_canvas.restoreState()
            overlay_canvas.showPage()
            overlay_canvas.save()

            overlay_stream.seek(0)
            watermark_pdf = PdfReader(overlay_stream)
            page.merge_page(watermark_pdf.pages[0])
            writer.add_page(page)

        output_stream = io.BytesIO()
        writer.write(output_stream)
        return output_stream.getvalue()

    @staticmethod
    def _calculate_gst_amount_paise(taxable_amount_paise: int, gst_rate_percent: int) -> int:
        if gst_rate_percent <= 0:
            return 0
        return int(
            (Decimal(taxable_amount_paise) * Decimal(gst_rate_percent) / Decimal("100")).quantize(
                Decimal("1"),
                rounding=ROUND_HALF_UP,
            )
        )

    @staticmethod
    def _gst_rate_for_digital_book(book: Book) -> int:
        # Digital story books and digital coloring books are taxed at 18% GST.
        _ = book
        return GST_RATE_DIGITAL_PERCENT

    async def send_invoice_email(
        self,
        *,
        order: DigitalBookOrder,
        user: User,
        book: Book | None,
        recipients: list[str],
    ) -> None:
        if not recipients:
            return

        if not settings.SMTP_HOST or not settings.SMTP_PORT:
            raise ServiceUnavailableException("SMTP is not configured")
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            raise ServiceUnavailableException("SMTP credentials are missing")

        book_name = book.book_name if book else f"Book #{order.book_id}"
        taxable_amount_paise = int(Decimal(str(book.price)) * 100) if book and book.price is not None else order.amount
        gst_rate_percent = self._gst_rate_for_digital_book(book) if book else 0
        gst_amount_paise = max(order.amount - taxable_amount_paise, 0)

        invoice_number = f"INV-DB-{order.id}-{datetime.now(timezone.utc):%Y%m%d}"
        invoice_pdf = self._build_invoice_pdf_bytes(
            invoice_number=invoice_number,
            order_id=str(order.id),
            customer_name=user.full_name or user.first_name,
            customer_email=user.email,
            item_name=book_name,
            taxable_amount_paise=taxable_amount_paise,
            gst_rate_percent=gst_rate_percent,
            gst_amount_paise=gst_amount_paise,
            total_amount_paise=order.amount,
            paid_at=order.paid_at,
            payment_id=order.razorpay_payment_id,
        )

        message = EmailMessage()
        message["Subject"] = f"Invoice for order #{order.id} - Panda Tales"
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = ", ".join(dict.fromkeys(recipients))
        message.set_content(
            "Hi,\n\n"
            "Thank you for your purchase on Panda Tales.\n"
            "Your tax invoice is attached as a PDF.\n\n"
            "Regards,\n"
            "Panda Tales"
        )

        message.add_attachment(
            invoice_pdf,
            maintype="application",
            subtype="pdf",
            filename=f"invoice-{order.id}.pdf",
        )

        await asyncio.to_thread(self._send_email_sync, message)

    def _build_invoice_pdf_bytes(
        self,
        *,
        invoice_number: str,
        order_id: str,
        customer_name: str,
        customer_email: str,
        item_name: str,
        taxable_amount_paise: int,
        gst_rate_percent: int,
        gst_amount_paise: int,
        total_amount_paise: int,
        paid_at: datetime | None,
        payment_id: str | None,
    ) -> bytes:
        buffer = io.BytesIO()
        page_w, page_h = A4
        pdf = canvas.Canvas(buffer, pagesize=A4)

        left = 50
        y = page_h - 50

        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(left, y, "TAX INVOICE")
        y -= 24
        pdf.setFont("Helvetica", 10)
        pdf.drawString(left, y, f"Seller: {settings.SMTP_FROM_NAME}")
        y -= 14
        pdf.drawString(left, y, f"Invoice No: {invoice_number}")
        y -= 14
        pdf.drawString(left, y, f"Order ID: {order_id}")
        y -= 14
        pdf.drawString(left, y, f"Invoice Date: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}")
        y -= 14
        if paid_at:
            pdf.drawString(left, y, f"Paid At: {paid_at:%Y-%m-%d %H:%M UTC}")
            y -= 14
        if payment_id:
            pdf.drawString(left, y, f"Payment ID: {payment_id}")
            y -= 14

        y -= 6
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(left, y, "Bill To")
        y -= 16
        pdf.setFont("Helvetica", 10)
        pdf.drawString(left, y, customer_name or "Customer")
        y -= 14
        pdf.drawString(left, y, customer_email)

        y -= 24
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(left, y, "Item")
        pdf.drawString(left + 260, y, "Taxable")
        pdf.drawString(left + 350, y, "GST")
        pdf.drawString(left + 430, y, "Total")
        y -= 10
        pdf.line(left, y, page_w - left, y)

        y -= 18
        pdf.setFont("Helvetica", 10)
        pdf.drawString(left, y, item_name)
        pdf.drawRightString(left + 330, y, f"INR {taxable_amount_paise / 100:.2f}")
        pdf.drawRightString(left + 420, y, f"{gst_rate_percent}%")
        pdf.drawRightString(page_w - left, y, f"INR {total_amount_paise / 100:.2f}")

        y -= 14
        pdf.drawString(left, y, f"GST Amount: INR {gst_amount_paise / 100:.2f}")
        y -= 20
        pdf.line(left, y, page_w - left, y)
        y -= 18
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(left, y, "Grand Total")
        pdf.drawRightString(page_w - left, y, f"INR {total_amount_paise / 100:.2f}")

        y -= 20
        pdf.setFont("Helvetica", 9)
        pdf.drawString(
            left,
            y,
            f"GST applied: {gst_rate_percent}% (Digital products: 18%, Physical books: 0% where applicable).",
        )

        pdf.showPage()
        pdf.save()
        return buffer.getvalue()
