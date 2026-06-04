"""Service layer for digital book catalog operations."""

import asyncio
import hashlib
import hmac
import io
import smtplib
import re
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from email.message import EmailMessage
from pathlib import Path
from uuid import uuid4

import ssl

import certifi
import razorpay
import urllib3
from jose import jwt
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, SSLError as RequestsSSLError
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import Color
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


GST_RATE_DIGITAL_PERCENT = 5
SUPPORTED_ATTRIBUTE_OPTION_TYPES = {"book_type", "style", "language", "genre"}
BOOK_TYPE_SEQUENCE = [
    "digital coloring book",
    "digital story book",
    "personalized coloring book",
    "personalised story book",
]
CANONICAL_BOOK_TYPES = set(BOOK_TYPE_SEQUENCE)
BOOK_TYPE_ALIASES = {
    "story": "digital story book",
    "story book": "digital story book",
    "digital story": "digital story book",
    "coloring": "digital coloring book",
    "coloring book": "digital coloring book",
    "digital coloring": "digital coloring book",
    "personalized story": "personalised story book",
    "personalized story book": "personalised story book",
    "personalised story": "personalised story book",
    "personalized coloring": "personalized coloring book",
    "personalised coloring": "personalized coloring book",
    "personalized coloring book": "personalized coloring book",
    "personalised coloring book": "personalized coloring book",
}
MIN_RAZORPAY_ORDER_AMOUNT_PAISE = 100
DOWNLOAD_TOKEN_TYPE = "digital_order_download"
DOWNLOAD_TOKEN_EXP_MINUTES = 15


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
        if self._payment_client is not None:
            if settings.RAZORPAY_VERIFY_SSL:
                self._payment_client.session.verify = certifi.where()
            else:
                # Build a permissive SSL context that bypasses both certificate
                # verification AND the minimum key-strength enforcement that causes
                # "EE certificate key too weak" errors behind corporate proxies.
                _ssl_ctx = ssl.create_default_context()
                _ssl_ctx.check_hostname = False
                _ssl_ctx.verify_mode = ssl.CERT_NONE
                _ssl_ctx.set_ciphers("DEFAULT:@SECLEVEL=0")

                class _WeakSSLAdapter(HTTPAdapter):
                    def init_poolmanager(self, *args, **kwargs):
                        kwargs["ssl_context"] = _ssl_ctx
                        super().init_poolmanager(*args, **kwargs)

                _adapter = _WeakSSLAdapter()
                self._payment_client.session.mount("https://", _adapter)
                self._payment_client.session.mount("http://", _adapter)
                self._payment_client.session.verify = False
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                logger.warning(
                    "razorpay_ssl_verification_disabled",
                    reason="RAZORPAY_VERIFY_SSL is false; use only for local troubleshooting",
                )

    async def create_book(
        self,
        data: DigitalBookCreateRequest,
        *,
        cover_image,
        front_image=None,
        back_image=None,
        page_1_image=None,
        page_2_image=None,
        page_3_image=None,
        page_4_image=None,
        book_file=None,
    ) -> Book:
        """Create digital book, upload files to MinIO, and persist object paths."""
        if not cover_image.content_type or not cover_image.content_type.startswith("image/"):
            raise BadRequestException("cover_image must be an image file")

        if front_image is not None and (
            not front_image.content_type or not front_image.content_type.startswith("image/")
        ):
            raise BadRequestException("front_image must be an image file")


        normalized_book_type = self._normalize_book_type_value(data.book_type)
        derived_is_personalized = self._is_personalized_book_type(normalized_book_type)
        if data.is_personalized != derived_is_personalized:
            raise BadRequestException("is_personalized must match selected book_type")

        page_uploads = [
            ("page_1_image", page_1_image),
            ("page_2_image", page_2_image),
            ("page_3_image", page_3_image),
            ("page_4_image", page_4_image),
        ]
        for page_name, page_file in page_uploads:
            if page_file is not None and (
                not page_file.content_type or not page_file.content_type.startswith("image/")
            ):
                raise BadRequestException(f"{page_name} must be an image file")
        if book_file is not None:
            book_ext = Path(book_file.filename or "").suffix.lower()
            if book_ext != ".pdf":
                raise BadRequestException("book_file must be a PDF")
        elif not derived_is_personalized:
            raise BadRequestException("book_file (PDF) is required for non-personalized books")

        genre = await self._get_or_create_genre(data.genre)
        normalized_category_id = await self._normalize_and_validate_category_id(data.category_id)
        category_row = await self._get_category_row(normalized_category_id)
        await self._validate_book_category_placement(
            category_row=category_row,
            category_id=normalized_category_id,
            is_personalized=derived_is_personalized,
        )
        if derived_is_personalized:
            personalized_kind = self._infer_personalized_kind(
                book_type=normalized_book_type,
                category_name=category_row.name,
            )
            if personalized_kind is None:
                raise BadRequestException(
                    "Personalized book must be either a story book or a coloring book"
                )
        book_type_id = await self._normalize_and_validate_attribute_option("book_type", normalized_book_type)
        style_id = await self._normalize_and_validate_attribute_option("style", data.style)
        language_id = await self._normalize_and_validate_attribute_option("language", data.language)

        book = Book(
            book_name=data.book_name,
            description=data.description,
            category_id=normalized_category_id,
            emoji=(data.emoji.strip() if data.emoji else None),
            age_label=(str(data.age_group).strip() if data.age_group else None),
            total_pages=data.total_pages,
            book_type_id=book_type_id,
            theme_id=style_id,
            language_id=language_id,
            genre_id=genre.id,
            price=float(data.price) if isinstance(data.price, Decimal) else data.price,
            rating=float(data.rating) if data.rating is not None else 0.0,
            total_ratings=data.total_ratings or 0,
            download_count=data.download_count or 0,
            is_bestseller=data.is_bestseller,
            is_personalized=derived_is_personalized,
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
            page_object_names: dict[str, str] = {}
            for idx, (_, page_file) in enumerate(page_uploads, start=1):
                if page_file is None:
                    continue
                page_ext = Path(page_file.filename or "").suffix.lower() or ".jpg"
                page_object_names[f"page_{idx}_image_url"] = f"digital-books/page_images/{slug}-{book.id}-page-{idx}{page_ext}"
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
            for idx, (page_name, page_file) in enumerate(page_uploads, start=1):
                if page_file is None:
                    continue
                object_name = page_object_names.get(f"page_{idx}_image_url")
                if not object_name:
                    continue
                await self.storage.upload_file(
                    file=page_file,
                    object_name=object_name,
                    content_type=page_file.content_type,
                    max_size_mb=10,
                )
                uploaded_objects.append(object_name)

            if book_file is not None:
                await self.storage.upload_file(
                    file=book_file,
                    object_name=book_object_name,
                    content_type="application/pdf",
                    max_size_mb=6144,
                )
                uploaded_objects.append(book_object_name)
                book.book_url = book_object_name

            book.cover_image_url = cover_object_name
            book.front_image_url = front_object_name if front_image else cover_object_name
            book.back_image_url = back_object_name if back_image else cover_object_name
            book.page_1_image_url = page_object_names.get("page_1_image_url")
            book.page_2_image_url = page_object_names.get("page_2_image_url")
            book.page_3_image_url = page_object_names.get("page_3_image_url")
            book.page_4_image_url = page_object_names.get("page_4_image_url")

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

    async def update_book_with_files(
        self,
        book_id: int,
        data: DigitalBookUpdateRequest,
        *,
        cover_image=None,
        front_image=None,
        back_image=None,
        page_1_image=None,
        page_2_image=None,
        page_3_image=None,
        page_4_image=None,
        book_file=None,
    ) -> dict:
        """Update metadata and optionally replace uploaded files for a digital book."""
        # First apply metadata validation/update logic.
        await self.update_book(book_id, data)

        book = await self.db.get(Book, book_id)
        if not book:
            raise NotFoundException("Book not found")

        image_files = [
            ("cover_image_url", cover_image),
            ("front_image_url", front_image),
            ("back_image_url", back_image),
            ("page_1_image_url", page_1_image),
            ("page_2_image_url", page_2_image),
            ("page_3_image_url", page_3_image),
            ("page_4_image_url", page_4_image),
        ]

        for field_name, image_file in image_files:
            if image_file is not None and (
                not image_file.content_type or not image_file.content_type.startswith("image/")
            ):
                raise BadRequestException(f"{field_name.replace('_url', '')} must be an image file")

        if book_file is not None:
            book_ext = Path(book_file.filename or "").suffix.lower()
            if book_ext != ".pdf":
                raise BadRequestException("book_file must be a PDF")

        has_file_updates = any(file_obj is not None for _, file_obj in image_files) or book_file is not None
        if not has_file_updates:
            return await self.get_book(book_id)

        slug = slugify(book.book_name) or f"book-{book.id}"
        uploaded_objects: list[str] = []
        old_objects: list[str] = []

        folder_map = {
            "cover_image_url": "cover_images",
            "front_image_url": "front_images",
            "back_image_url": "back_images",
            "page_1_image_url": "page_images",
            "page_2_image_url": "page_images",
            "page_3_image_url": "page_images",
            "page_4_image_url": "page_images",
        }

        try:
            for field_name, image_file in image_files:
                if image_file is None:
                    continue

                ext = Path(image_file.filename or "").suffix.lower() or ".jpg"
                suffix = ""
                if field_name.startswith("page_"):
                    page_num = field_name.split("_")[1]
                    suffix = f"-page-{page_num}"
                object_name = f"digital-books/{folder_map[field_name]}/{slug}-{book.id}{suffix}-{uuid4().hex[:8]}{ext}"

                await self.storage.upload_file(
                    file=image_file,
                    object_name=object_name,
                    content_type=image_file.content_type,
                    max_size_mb=10,
                )
                uploaded_objects.append(object_name)

                old_value = getattr(book, field_name, None)
                if old_value and old_value != object_name:
                    old_objects.append(old_value)
                setattr(book, field_name, object_name)

            if book_file is not None:
                pdf_object_name = f"digital-books/books/{slug}-{book.id}-{uuid4().hex[:8]}.pdf"
                await self.storage.upload_file(
                    file=book_file,
                    object_name=pdf_object_name,
                    content_type="application/pdf",
                    max_size_mb=6144,
                )
                uploaded_objects.append(pdf_object_name)

                if book.book_url and book.book_url != pdf_object_name:
                    old_objects.append(book.book_url)
                book.book_url = pdf_object_name

            await self.db.commit()
            await self.db.refresh(book)
        except Exception:
            await self.db.rollback()
            for object_name in uploaded_objects:
                try:
                    await self.storage.delete_file(object_name)
                except Exception:
                    logger.warning("digital_book_update_cleanup_failed", object_name=object_name)
            raise

        for object_name in old_objects:
            try:
                await self.storage.delete_file(object_name)
            except Exception:
                logger.warning("digital_book_old_asset_delete_failed", object_name=object_name)

        return await self.get_book(book_id)

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
            normalized_book_type = self._normalize_book_type_value(book_type)
            query = query.where(
                Book.book_type_id.in_(
                    select(BookAttributeOption.id).where(
                        BookAttributeOption.option_type == "book_type",
                        BookAttributeOption.value == normalized_book_type,
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
        for book, genre_name, category_name, category_tag, category_description, book_type_val, style_val, language_val in rows:
            items.append(
                await self._to_response_dict(
                    book,
                    genre_name=genre_name,
                    include_pdf_url=False,
                    category_name=category_name,
                    category_tag=category_tag,
                    category_description=category_description,
                    book_type=book_type_val,
                    style=style_val,
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

        book, genre_name, category_name, category_tag, category_description, book_type_val, style_val, language_val = row
        return await self._to_response_dict(
            book,
            genre_name=genre_name,
            include_pdf_url=False,
            category_name=category_name,
            category_tag=category_tag,
            category_description=category_description,
            book_type=book_type_val,
            style=style_val,
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
        response_rows: list[dict] = []
        for row in rows:
            category_image_presigned_url = await self._presign_category_image_url(
                row.category_image_url,
                row.category_id,
            )
            response_rows.append(
                {
                    "id": row.id,
                    "category_id": row.category_id,
                    "name": row.name,
                    "tags": self._split_tags(row.personalized_tag),
                    "personalized_tag": row.personalized_tag,
                    "description": row.description,
                    "category_image_url": row.category_image_url,
                    "category_image_presigned_url": category_image_presigned_url,
                    "emoji": row.emoji,
                    "color": row.color,
                    "grad": row.grad,
                    "personalized": row.personalized,
                    "is_active": row.is_active,
                    "label": row.label,
                    "category_type": row.category_type,
                }
            )
        return response_rows

    async def create_or_update_category(self, payload: BookCategoryCreateRequest, category_image=None) -> dict:
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

        old_category_image_url: str | None = None

        if row is None:
            normalized_category_tag = self._merge_tags_to_storage(payload.tags, None)
            row = BookCategory(
                category_id=normalized_id,
                name=payload.name.strip(),
                personalized_tag=normalized_category_tag,
                label=payload.label,
                description=payload.description,
            category_image_url=getattr(payload, "category_image_url", None),
                emoji=payload.emoji,
                color=payload.color,
                grad=payload.grad,
                personalized=payload.personalized,
                is_active=payload.is_active,
                category_type=getattr(payload, "category_type", None),
            )
            self.db.add(row)
        else:
            mismatch_count_result = await self.db.execute(
                select(func.count(Book.id)).where(
                    Book.category_id == normalized_id,
                    Book.is_personalized != payload.personalized,
                )
            )
            mismatch_count = int(mismatch_count_result.scalar_one() or 0)
            if mismatch_count > 0:
                raise BadRequestException(
                    "Cannot change category type because existing books in this category use the opposite type"
                )

            old_category_image_url = row.category_image_url
            row.name = payload.name.strip()
            row.personalized_tag = self._merge_tags_to_storage(payload.tags, None)
            row.label = payload.label
            row.description = payload.description
            if getattr(payload, "category_image_url", None) is not None:
                row.category_image_url = payload.category_image_url
            row.emoji = payload.emoji
            row.color = payload.color
            row.grad = payload.grad
            row.personalized = payload.personalized
            row.is_active = payload.is_active
            row.category_type = getattr(payload, "category_type", None)

        if category_image is not None:
            content_type = getattr(category_image, "content_type", None) or ""
            if not str(content_type).startswith("image/"):
                raise BadRequestException("category_image must be an image file")

            file_ext = Path(getattr(category_image, "filename", "") or "").suffix.lower() or ".jpg"
            slug = slugify(payload.name) or f"category-{normalized_id}"
            object_name = f"digital-books/category-images/{slug}-{normalized_id}-{uuid4().hex[:8]}{file_ext}"
            await self.storage.upload_file(
                file=category_image,
                object_name=object_name,
                content_type=content_type,
                max_size_mb=10,
            )
            row.category_image_url = object_name

        await self.db.commit()
        await self.db.refresh(row)

        if (
            old_category_image_url
            and row.category_image_url
            and old_category_image_url != row.category_image_url
        ):
            try:
                await self.storage.delete_file(old_category_image_url)
            except Exception:
                logger.warning(
                    "category_image_delete_old_failed",
                    category_id=row.category_id,
                    object_name=old_category_image_url,
                )

        category_image_presigned_url = await self._presign_category_image_url(
            row.category_image_url,
            row.category_id,
        )

        return {
            "id": row.id,
            "category_id": row.category_id,
            "name": row.name,
            "tags": self._split_tags(row.personalized_tag),
            "personalized_tag": row.personalized_tag,
            "label": row.label,
            "description": row.description,
            "category_image_url": row.category_image_url,
            "category_image_presigned_url": category_image_presigned_url,
            "emoji": row.emoji,
            "color": row.color,
            "grad": row.grad,
            "personalized": row.personalized,
            "is_active": row.is_active,
            "category_type": row.category_type,
        }

    async def add_book_category(self, book_id: int, category_id: int) -> dict:
        """Assign or update category for a book."""
        book = await self.db.get(Book, book_id)
        if not book:
            raise NotFoundException("Book not found")

        validated = await self._normalize_and_validate_category_id(category_id)
        if validated is None:
            raise BadRequestException("category_id is required")

        category_row = await self._get_category_row(validated)
        await self._validate_book_category_placement(
            category_row=category_row,
            category_id=validated,
            is_personalized=book.is_personalized,
        )

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
        if data.category_id is not None:
            book.category_id = await self._normalize_and_validate_category_id(data.category_id)
        if data.emoji is not None:
            book.emoji = data.emoji.strip()
        if data.age_group is not None:
            book.age_label = str(data.age_group).strip() or None
        if data.total_pages is not None:
            book.total_pages = data.total_pages
        if data.book_type is not None:
            normalized_book_type = self._normalize_book_type_value(data.book_type)
            book.book_type_id = await self._normalize_and_validate_attribute_option("book_type", normalized_book_type)
        if data.style is not None:
            book.theme_id = await self._normalize_and_validate_attribute_option("style", data.style)
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
        book_type_value = await self._get_attribute_option_value(book.book_type_id)
        if not book_type_value:
            raise BadRequestException("book_type is required")
        normalized_existing_book_type = self._normalize_book_type_value(book_type_value)
        if normalized_existing_book_type != book_type_value:
            book.book_type_id = await self._normalize_and_validate_attribute_option(
                "book_type", normalized_existing_book_type
            )
        derived_is_personalized = self._is_personalized_book_type(normalized_existing_book_type)
        if data.is_personalized is not None and data.is_personalized != derived_is_personalized:
            raise BadRequestException("is_personalized must match selected book_type")
        book.is_personalized = derived_is_personalized

        category_row = await self._get_category_row(book.category_id)
        await self._validate_book_category_placement(
            category_row=category_row,
            category_id=book.category_id,
            is_personalized=book.is_personalized,
        )
        if book.is_personalized:
            personalized_kind = self._infer_personalized_kind(
                book_type=normalized_existing_book_type,
                category_name=category_row.name,
            )
            if personalized_kind is None:
                raise BadRequestException(
                    "Personalized book must be either a story book or a coloring book"
                )

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
            book_row, genre_name, category_name, category_tag, category_description, book_type_val, style_val, language_val = row
            return await self._to_response_dict(
                book_row,
                genre_name=genre_name,
                include_pdf_url=False,
                category_name=category_name,
                category_tag=category_tag,
                category_description=category_description,
                book_type=book_type_val,
                style=style_val,
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
        """Return filter options from existing catalog data."""

        genres_result = await self.db.execute(select(Genre.name).order_by(Genre.name.asc()))
        genres = [name for name in genres_result.scalars().all() if name]

        options_result = await self.db.execute(
            select(BookAttributeOption)
            .where(BookAttributeOption.is_active.is_(True))
            .order_by(BookAttributeOption.option_type.asc(), BookAttributeOption.value.asc())
        )
        option_rows = options_result.scalars().all()

        grouped: dict[str, list[str]] = {"book_type": [], "style": [], "language": []}
        for row in option_rows:
            values = grouped.get(row.option_type)
            if values is not None:
                values.append(row.value)

        return {
            "book_types": grouped["book_type"],
            "styles": grouped["style"],
            "languages": grouped["language"],
            "genres": genres,
        }

    async def list_attribute_options(self) -> dict[str, list[str]]:
        """Return admin-managed dropdown values for book metadata fields."""
        filter_options = await self.get_filter_options()
        return {
            "book_type": BOOK_TYPE_SEQUENCE,
            "style": filter_options.get("styles", []),
            "language": filter_options.get("languages", []),
            "genre": filter_options.get("genres", []),
        }

    async def create_attribute_option(self, option_type: str, value: str) -> dict[str, str]:
        normalized_type = self._normalize_option_type(option_type)
        if normalized_type == "book_type":
            raise BadRequestException("book_type options are fixed and cannot be added")
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
        if normalized_type == "book_type":
            raise BadRequestException("book_type options are fixed and cannot be deleted")
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
            "style": Book.theme_id,
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

        if not user or not getattr(user, "is_active", False):
            raise BadRequestException("User does not exist or is inactive")

        book = await self.db.get(Book, payload.book_id)
        if not book:
            raise NotFoundException("Book not found")

        if book.price is None:
            raise BadRequestException("Book price is missing")

        delivery_method = "browser_download"
        delivery_contact = (user.email or "browser").strip() or "browser"
        taxable_amount_paise = int(Decimal(str(book.price)) * 100)
        gst_rate_percent = self._gst_rate_for_digital_book(book)
        gst_amount_paise = self._calculate_gst_amount_paise(
            taxable_amount_paise,
            gst_rate_percent,
        )
        total_amount_paise = taxable_amount_paise + gst_amount_paise

        if total_amount_paise < MIN_RAZORPAY_ORDER_AMOUNT_PAISE:
            minimum_inr = Decimal(MIN_RAZORPAY_ORDER_AMOUNT_PAISE) / Decimal(100)
            raise BadRequestException(
                f"Order total (INR {total_amount_paise / 100:.2f}) is below Razorpay minimum "
                f"(INR {minimum_inr:.2f}). Increase book price and try again."
            )

        try:
            rz_order = self._payment_client.order.create(
                {
                    "amount": total_amount_paise,
                    "currency": "INR",
                    "payment_capture": 1,
                    "notes": {
                        "book_id": str(book.id),
                        "user_id": str(user.id),
                        "delivery_method": delivery_method,
                        "delivery_contact": delivery_contact,
                        "taxable_amount": str(taxable_amount_paise),
                        "gst_rate_percent": str(gst_rate_percent),
                        "gst_amount": str(gst_amount_paise),
                    },
                }
            )
        except razorpay.errors.BadRequestError as exc:
            logger.error("razorpay_order_bad_request", error=str(exc), amount_paise=total_amount_paise)
            raise BadRequestException(f"Payment gateway rejected order: {exc}") from exc
        except RequestsSSLError as exc:
            logger.error(
                "razorpay_ssl_error",
                error=str(exc),
                verify_ssl=settings.RAZORPAY_VERIFY_SSL,
                exc_info=True,
            )
            raise ServiceUnavailableException(
                "Unable to connect to Razorpay due to SSL certificate validation. "
                "Check system/proxy certificates or set RAZORPAY_VERIFY_SSL=false for local development only."
            ) from exc
        except RequestException as exc:
            logger.error("razorpay_network_error", error=str(exc), exc_info=True)
            raise ServiceUnavailableException(
                "Payment gateway is temporarily unavailable. Please try again in a few minutes."
            ) from exc

        order = DigitalBookOrder(
            user_id=user.id,
            book_id=book.id,
            delivery_method=delivery_method,
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
            history_item = await self._payment_history_item(order)
            history_item["download_urls"] = await self._build_download_urls(order)
            return history_item

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

        if not book:
            raise NotFoundException("Book not found")

        invoice_result = await self.create_and_email_razorpay_invoice(
            order=order,
            user=user,
            book=book,
        )
        order.delivery_method = "browser_download"
        order.delivery_contact = (user.email or "browser").strip() or "browser"
        order.delivery_status = "ready"
        order.delivery_sent_at = datetime.now(timezone.utc)
        order.status = "delivered"

        await self.db.commit()
        await self.db.refresh(order)
        response = await self._payment_history_item(order)
        response["invoice_email_sent"] = invoice_result.get("invoice_email_sent", False)
        response["invoice_razorpay_id"] = invoice_result.get("invoice_razorpay_id")
        response["invoice_razorpay_number"] = invoice_result.get("invoice_razorpay_number")
        response["download_urls"] = await self._build_download_urls(order)
        return response

    async def _build_download_urls(self, order: DigitalBookOrder) -> dict[str, str]:
        """Return short-lived same-origin download links for browser-safe downloads."""
        book = await self.db.get(Book, order.book_id)
        if not book:
            return {}

        download_urls: dict[str, str] = {}
        if book.book_url:
            book_token = self._create_order_download_token(
                user_id=str(order.user_id),
                order_id=order.id,
                file_type="book",
            )
            download_urls["book"] = (
                f"/api/v1/payments/digital-books/{order.id}/download/book/public?token={book_token}"
            )

        cover_source = book.cover_image_url or book.front_image_url or book.back_image_url
        if cover_source:
            cover_token = self._create_order_download_token(
                user_id=str(order.user_id),
                order_id=order.id,
                file_type="cover",
            )
            download_urls["cover"] = (
                f"/api/v1/payments/digital-books/{order.id}/download/cover/public?token={cover_token}"
            )

        return download_urls

    @staticmethod
    def _create_order_download_token(*, user_id: str, order_id: int, file_type: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=DOWNLOAD_TOKEN_EXP_MINUTES)
        payload = {
            "sub": user_id,
            "order_id": order_id,
            "file_type": file_type,
            "type": DOWNLOAD_TOKEN_TYPE,
            "exp": expire,
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    async def save_purchase_artifacts_locally(
        self,
        *,
        order: DigitalBookOrder,
        user: User,
        book: Book,
    ) -> dict[str, str]:
        """Save paid order artifacts (cover and PDF) to local disk."""
        if not book.book_url:
            raise BadRequestException("Book PDF URL is missing")

        base_dir = Path(settings.LOCAL_DIGITAL_DELIVERY_DIR)
        timestamp_label = (order.paid_at or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M%S")
        order_dir_name = f"order-{order.id}-{timestamp_label}"
        order_dir = base_dir / order_dir_name
        order_dir.mkdir(parents=True, exist_ok=True)

        safe_book_name = slugify(book.book_name) or f"book-{book.id}"

        pdf_bytes = await self.storage.download_file(book.book_url)
        pdf_filename = f"{safe_book_name}-{order.id}.pdf"
        pdf_path = order_dir / pdf_filename
        await asyncio.to_thread(pdf_path.write_bytes, pdf_bytes)

        cover_source = book.cover_image_url or book.front_image_url or book.back_image_url
        cover_filename = ""
        if cover_source:
            cover_bytes = await self.storage.download_file(cover_source)
            cover_ext = Path(cover_source).suffix.lower() or ".jpg"
            cover_filename = f"{safe_book_name}-cover-{order.id}{cover_ext}"
            cover_path = order_dir / cover_filename
            await asyncio.to_thread(cover_path.write_bytes, cover_bytes)

        logger.info(
            "digital_order_saved_locally",
            order_id=order.id,
            order_dir=str(order_dir),
            pdf_file=pdf_filename,
            cover_file=cover_filename,
        )

        return {
            "order_directory": str(order_dir).replace("\\", "/"),
            "pdf_file": pdf_filename,
            "cover_file": cover_filename,
        }

    async def create_and_email_razorpay_invoice(
        self,
        *,
        order: DigitalBookOrder,
        user: User,
        book: Book,
    ) -> dict[str, str | bool | None]:
        """Create Razorpay invoice and trigger invoice email to registered user."""
        taxable_amount_paise = int(Decimal(str(book.price)) * 100) if book.price is not None else order.amount
        gst_rate_percent = self._gst_rate_for_digital_book(book)
        gst_amount_paise = max(order.amount - taxable_amount_paise, 0)
        invoice_number = f"INV-{datetime.now(timezone.utc):%Y}-{order.id:06d}"
        invoice_receipt = invoice_number
        customer_name = (user.full_name or user.first_name or "Customer").strip() or "Customer"
        customer_contact = ""
        if user.phone:
            customer_contact = "".join(ch for ch in str(user.phone) if ch.isdigit())
        if customer_contact and len(customer_contact) < 10:
            customer_contact = ""

        is_intra_state = self._is_intra_state_supply()
        igst_amount_paise, cgst_amount_paise, sgst_amount_paise = self._split_gst_components(
            gst_amount_paise,
            is_intra_state=is_intra_state,
        )

        invoice_payload: dict = {
            "type": "invoice",
            "draft": 0,
            "currency": "INR",
            "receipt": invoice_receipt,
            "description": f"Digital book purchase - Order #{order.id}",
            "customer": {
                "name": customer_name,
                "email": user.email,
                "contact": customer_contact,
            },
            "line_items": [
                {
                    "name": book.book_name,
                    "description": "Digital book (taxable amount)",
                    "amount": taxable_amount_paise,
                    "currency": "INR",
                    "quantity": 1,
                    "hsn_code": "99843",
                },
                {
                    "name": f"GST @{gst_rate_percent}%",
                    "description": "GST component",
                    "amount": gst_amount_paise,
                    "currency": "INR",
                    "quantity": 1,
                    "hsn_code": "99843",
                },
            ],
            "email_notify": 1,
            "sms_notify": 0,
            "notes": {
                "order_id": str(order.id),
                "payment_id": order.razorpay_payment_id or "",
                "seller_gstin": settings.SELLER_GSTIN,
                "customer_name": customer_name,
                "customer_email": user.email,
                "customer_contact": customer_contact,
                "hsn_sac": "99843",
                "taxable_amount_inr": f"{taxable_amount_paise / 100:.2f}",
                "gst_rate_percent": str(gst_rate_percent),
                "igst_inr": f"{igst_amount_paise / 100:.2f}",
                "cgst_inr": f"{cgst_amount_paise / 100:.2f}",
                "sgst_inr": f"{sgst_amount_paise / 100:.2f}",
            },
        }

        if not customer_contact:
            invoice_payload["customer"].pop("contact", None)

        if not self._payment_client:
            smtp_sent = await self._send_digital_invoice_email(
                order=order,
                user=user,
                book=book,
                invoice_number=invoice_number,
                taxable_amount_paise=taxable_amount_paise,
                gst_rate_percent=gst_rate_percent,
                gst_amount_paise=gst_amount_paise,
            )
            return {
                "invoice_email_sent": smtp_sent,
                "invoice_razorpay_id": None,
                "invoice_razorpay_number": None,
            }

        try:
            rz_invoice = await asyncio.to_thread(self._payment_client.invoice.create, invoice_payload)
            invoice_id = rz_invoice.get("id")
            invoice_number = rz_invoice.get("invoice_number") or invoice_number
            notify_sent = False

            try:
                if invoice_id:
                    await asyncio.to_thread(self._payment_client.invoice.notify_by, invoice_id, "email")
                    notify_sent = True
            except Exception:
                logger.warning(
                    "razorpay_invoice_notify_failed",
                    order_id=order.id,
                    invoice_id=invoice_id,
                )

            smtp_sent = False
            try:
                smtp_sent = await self._send_digital_invoice_email(
                    order=order,
                    user=user,
                    book=book,
                    invoice_number=invoice_number,
                    taxable_amount_paise=taxable_amount_paise,
                    gst_rate_percent=gst_rate_percent,
                    gst_amount_paise=gst_amount_paise,
                )
            except Exception as exc:
                logger.warning(
                    "digital_invoice_smtp_fallback_failed",
                    order_id=order.id,
                    email=user.email,
                    error=str(exc),
                )

            logger.info(
                "razorpay_invoice_created",
                order_id=order.id,
                invoice_id=invoice_id,
                invoice_number=invoice_number,
                email=user.email,
            )

            if not (notify_sent or smtp_sent):
                logger.warning(
                    "digital_invoice_not_sent",
                    order_id=order.id,
                    invoice_id=invoice_id,
                    email=user.email,
                    reason="Razorpay notify and SMTP fallback both unavailable/failed",
                )

            return {
                "invoice_email_sent": bool(notify_sent or smtp_sent),
                "invoice_razorpay_id": invoice_id,
                "invoice_razorpay_number": invoice_number,
            }
        except Exception as exc:
            smtp_sent = False
            try:
                smtp_sent = await self._send_digital_invoice_email(
                    order=order,
                    user=user,
                    book=book,
                    invoice_number=invoice_number,
                    taxable_amount_paise=taxable_amount_paise,
                    gst_rate_percent=gst_rate_percent,
                    gst_amount_paise=gst_amount_paise,
                )
            except Exception as email_exc:
                logger.warning(
                    "digital_invoice_email_fallback_after_razorpay_failure_failed",
                    order_id=order.id,
                    email=user.email,
                    error=str(email_exc),
                )

            logger.error(
                "razorpay_invoice_create_failed",
                order_id=order.id,
                email=user.email,
                error=str(exc),
                exc_info=True,
            )
            return {
                "invoice_email_sent": smtp_sent,
                "invoice_razorpay_id": None,
                "invoice_razorpay_number": None,
            }

    async def _send_digital_invoice_email(
        self,
        *,
        order: DigitalBookOrder,
        user: User,
        book: Book,
        invoice_number: str,
        taxable_amount_paise: int,
        gst_rate_percent: int,
        gst_amount_paise: int,
    ) -> bool:
        if not settings.SMTP_HOST or not settings.SMTP_PORT:
            return False
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            return False
        if not user.email:
            return False

        total_amount_paise = order.amount
        customer_name = (user.full_name or user.first_name or "Customer").strip() or "Customer"
        customer_phone = (user.phone or "").strip() or "Unavailable"
        igst_amount_paise, cgst_amount_paise, sgst_amount_paise = self._split_gst_components(
            gst_amount_paise,
            is_intra_state=self._is_intra_state_supply(),
        )

        invoice_pdf = self._build_digital_invoice_pdf_bytes(
            invoice_number=invoice_number,
            order=order,
            book=book,
            customer_name=customer_name,
            customer_email=user.email,
            customer_phone=customer_phone,
            taxable_amount_paise=taxable_amount_paise,
            gst_rate_percent=gst_rate_percent,
            gst_amount_paise=gst_amount_paise,
            igst_amount_paise=igst_amount_paise,
            cgst_amount_paise=cgst_amount_paise,
            sgst_amount_paise=sgst_amount_paise,
            total_amount_paise=total_amount_paise,
        )

        message = EmailMessage()
        message["Subject"] = f"GST Invoice for digital order #{order.id} - Panda Tales"
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = user.email
        message.set_content(
            f"Hi {customer_name},\n\n"
            "Thanks for your digital purchase with Panda Tales.\n"
            "Please find your GST invoice attached.\n\n"
            f"Invoice Number: {invoice_number}\n"
            f"Customer Name: {customer_name}\n"
            f"Customer Email: {user.email}\n"
            f"Customer Phone: {customer_phone}\n"
            f"Book: {book.book_name}\n"
            "HSN/SAC: 99843\n"
            f"Taxable Amount: INR {taxable_amount_paise / 100:.2f}\n"
            f"GST ({gst_rate_percent}%): INR {gst_amount_paise / 100:.2f}\n"
            f"IGST: INR {igst_amount_paise / 100:.2f}\n"
            f"CGST: INR {cgst_amount_paise / 100:.2f}\n"
            f"SGST: INR {sgst_amount_paise / 100:.2f}\n"
            f"Grand Total: INR {total_amount_paise / 100:.2f}\n\n"
            "Regards,\n"
            "Panda Tales"
        )
        message.add_attachment(
            invoice_pdf,
            maintype="application",
            subtype="pdf",
            filename=f"digital-invoice-{order.id}.pdf",
        )

        await asyncio.to_thread(self._send_email_sync, message)
        return True

    @staticmethod
    def _send_email_sync(message: EmailMessage) -> None:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)

    def _build_digital_invoice_pdf_bytes(
        self,
        *,
        invoice_number: str,
        order: DigitalBookOrder,
        book: Book,
        customer_name: str,
        customer_email: str,
        customer_phone: str,
        taxable_amount_paise: int,
        gst_rate_percent: int,
        gst_amount_paise: int,
        igst_amount_paise: int,
        cgst_amount_paise: int,
        sgst_amount_paise: int,
        total_amount_paise: int,
    ) -> bytes:
        buffer = io.BytesIO()
        page_w, page_h = A4
        pdf = canvas.Canvas(buffer, pagesize=A4)

        left = 50
        right = page_w - 50
        y = page_h - 50

        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(left, y, "TAX INVOICE")
        pdf.setFont("Helvetica", 9)
        pdf.drawString(left, y - 14, "Panda Tales")

        meta_x = right - 230
        meta_top = y + 8
        meta_bottom = y - 72
        pdf.rect(meta_x, meta_bottom, 230, meta_top - meta_bottom)
        pdf.setFont("Helvetica", 9)
        pdf.drawString(meta_x + 10, meta_top - 14, f"Invoice No: {invoice_number}")
        pdf.drawString(meta_x + 10, meta_top - 28, f"Invoice Date: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}")
        pdf.drawString(meta_x + 10, meta_top - 42, f"Order ID: {order.id}")
        if order.razorpay_payment_id:
            pdf.drawString(meta_x + 10, meta_top - 56, f"Payment ID: {order.razorpay_payment_id}")
        elif order.paid_at:
            pdf.drawString(meta_x + 10, meta_top - 56, f"Paid At: {order.paid_at:%Y-%m-%d %H:%M UTC}")

        y = meta_bottom - 16
        box_h = 68
        gap = 12
        half_w = (right - left - gap) / 2

        pdf.rect(left, y - box_h, half_w, box_h)
        pdf.rect(left + half_w + gap, y - box_h, half_w, box_h)

        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(left + 8, y - 14, "Bill To")
        pdf.drawString(left + half_w + gap + 8, y - 14, "Seller")

        pdf.setFont("Helvetica", 9)
        pdf.drawString(left + 8, y - 30, customer_name)
        pdf.drawString(left + 8, y - 44, customer_email)
        pdf.drawString(left + 8, y - 58, customer_phone)

        pdf.drawString(left + half_w + gap + 8, y - 30, settings.SMTP_FROM_NAME)
        pdf.drawString(left + half_w + gap + 8, y - 44, f"GSTIN: {settings.SELLER_GSTIN}")
        pdf.drawString(left + half_w + gap + 8, y - 58, "Country: India")

        y -= box_h + 20

        table_top = y
        row_h = 20
        table_rows = 2
        table_h = row_h * table_rows
        col_widths = [26, 184, 66, 80, 44, 70, 76]
        table_w = sum(col_widths)

        pdf.rect(left, table_top - table_h, table_w, table_h)
        x = left
        for w in col_widths[:-1]:
            x += w
            pdf.line(x, table_top, x, table_top - table_h)
        pdf.line(left, table_top - row_h, left + table_w, table_top - row_h)

        pdf.setFillColor(Color(0.95, 0.95, 0.95))
        pdf.rect(left, table_top - row_h, table_w, row_h, fill=1, stroke=0)
        pdf.setFillColor(Color(0, 0, 0))

        headers = ["#", "Description", "HSN/SAC", "Taxable", "GST %", "GST Amt", "Total"]
        x = left
        pdf.setFont("Helvetica-Bold", 9)
        for idx, title in enumerate(headers):
            align_right = idx in (3, 5, 6)
            if align_right:
                pdf.drawRightString(x + col_widths[idx] - 4, table_top - 14, title)
            else:
                pdf.drawString(x + 4, table_top - 14, title)
            x += col_widths[idx]

        values = [
            "1",
            f"{book.book_name} (Digital)",
            "99843",
            f"INR {taxable_amount_paise / 100:.2f}",
            f"{gst_rate_percent}%",
            f"INR {gst_amount_paise / 100:.2f}",
            f"INR {total_amount_paise / 100:.2f}",
        ]
        x = left
        pdf.setFont("Helvetica", 9)
        for idx, value in enumerate(values):
            align_right = idx in (3, 5, 6)
            if align_right:
                pdf.drawRightString(x + col_widths[idx] - 4, table_top - row_h - 14, value)
            else:
                pdf.drawString(x + 4, table_top - row_h - 14, value)
            x += col_widths[idx]

        y = table_top - table_h - 16

        summary_w = 230
        summary_h = 92
        summary_x = right - summary_w
        pdf.rect(summary_x, y - summary_h, summary_w, summary_h)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(summary_x + 8, y - 14, "Tax Summary")
        pdf.setFont("Helvetica", 9)
        pdf.drawString(summary_x + 8, y - 30, f"IGST: INR {igst_amount_paise / 100:.2f}")
        pdf.drawString(summary_x + 8, y - 44, f"CGST: INR {cgst_amount_paise / 100:.2f}")
        pdf.drawString(summary_x + 8, y - 58, f"SGST: INR {sgst_amount_paise / 100:.2f}")
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(summary_x + 8, y - 78, "Grand Total")
        pdf.drawRightString(summary_x + summary_w - 8, y - 78, f"INR {total_amount_paise / 100:.2f}")

        pdf.setFont("Helvetica", 8)
        pdf.drawString(left, y - summary_h - 14, "GST summary: Digital products 5%.")

        pdf.showPage()
        pdf.save()
        return buffer.getvalue()

    @staticmethod
    def _split_gst_components(gst_amount_paise: int, *, is_intra_state: bool) -> tuple[int, int, int]:
        if gst_amount_paise <= 0:
            return 0, 0, 0
        if not is_intra_state:
            return gst_amount_paise, 0, 0
        cgst = gst_amount_paise // 2
        sgst = gst_amount_paise - cgst
        return 0, cgst, sgst

    @staticmethod
    def _is_intra_state_supply() -> bool:
        return bool(settings.GST_INTRA_STATE_BY_DEFAULT)

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
        if normalized_type == "book_type":
            normalized_value = self._normalize_book_type_value(normalized_value)

            option_id = await self._ensure_book_type_option(normalized_value)
            return option_id

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

    async def _ensure_book_type_option(self, normalized_value: str) -> int:
        result = await self.db.execute(
            select(BookAttributeOption).where(
                BookAttributeOption.option_type == "book_type",
                BookAttributeOption.value == normalized_value,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            if not row.is_active:
                row.is_active = True
                await self.db.flush()
            return int(row.id)

        row = BookAttributeOption(option_type="book_type", value=normalized_value, is_active=True)
        self.db.add(row)
        await self.db.flush()
        return int(row.id)

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

    @staticmethod
    def _normalize_book_type_value(value: str) -> str:
        normalized = (value or "").strip().lower()
        normalized = re.sub(r"\s+", " ", normalized)
        normalized = BOOK_TYPE_ALIASES.get(normalized, normalized)
        if normalized not in CANONICAL_BOOK_TYPES:
            has_personal = "personal" in normalized
            has_story = "story" in normalized or "tale" in normalized
            has_coloring = "color" in normalized

            if has_personal and has_story:
                normalized = "personalised story book"
            elif has_personal and has_coloring:
                normalized = "personalized coloring book"
            elif has_story:
                normalized = "digital story book"
            elif has_coloring:
                normalized = "digital coloring book"

        if normalized not in CANONICAL_BOOK_TYPES:
            raise BadRequestException(
                "book_type must be one of: digital coloring book, digital story book, personalized coloring book, personalised story book"
            )
        return normalized

    def _normalize_book_type_for_response(
        self,
        *,
        book_type: str | None,
        is_personalized: bool,
        category_name: str | None,
    ) -> str:
        if book_type:
            try:
                return self._normalize_book_type_value(book_type)
            except BadRequestException:
                logger.warning(
                    "digital_book_type_normalized_from_legacy_value",
                    raw_book_type=book_type,
                    is_personalized=is_personalized,
                    category_name=category_name,
                )

        inferred_kind = self._infer_personalized_kind(book_type=book_type, category_name=category_name)

        if is_personalized:
            if inferred_kind == "coloring":
                return "personalized coloring book"
            return "personalised story book"

        if inferred_kind == "coloring":
            return "digital coloring book"
        return "digital story book"

    @staticmethod
    def _is_personalized_book_type(book_type: str) -> bool:
        return "personal" in (book_type or "")

    async def _to_response_dict(
        self,
        book: Book,
        genre_name: str | None,
        include_pdf_url: bool,
        category_name: str | None = None,
        category_tag: str | None = None,
        category_description: str | None = None,
        book_type: str | None = None,
        style: str | None = None,
        language: str | None = None,
    ) -> dict:
        cover_presigned_url = await self._presign_url(book.cover_image_url, book.id, "cover")
        front_presigned_url = await self._presign_url(book.front_image_url, book.id, "front")
        back_presigned_url = await self._presign_url(book.back_image_url, book.id, "back")
        page_1_presigned_url = await self._presign_url(book.page_1_image_url, book.id, "page_1")
        page_2_presigned_url = await self._presign_url(book.page_2_image_url, book.id, "page_2")
        page_3_presigned_url = await self._presign_url(book.page_3_image_url, book.id, "page_3")
        page_4_presigned_url = await self._presign_url(book.page_4_image_url, book.id, "page_4")

        normalized_response_book_type = self._normalize_book_type_for_response(
            book_type=book_type,
            is_personalized=book.is_personalized,
            category_name=category_name,
        )

        response_is_personalized = self._is_personalized_book_type(normalized_response_book_type)

        personalized_kind = (
            self._infer_personalized_kind(book_type=normalized_response_book_type, category_name=category_name)
            if response_is_personalized
            else None
        )

        return {
            "id": book.id,
            "book_name": book.book_name,
            "description": book.description,
            "category_id": book.category_id,
            "category": book.category_id,
            "category_name": category_name,
            "category_tag": category_tag,
            "category_tags": self._split_tags(category_tag),
            "category_description": category_description,
            "emoji": book.emoji,
            "is_bestseller": book.is_bestseller,
            "is_personalized": response_is_personalized,
            "personalized_kind": personalized_kind,
            "cover_image_url": book.cover_image_url,
            "cover_image_presigned_url": cover_presigned_url,
            "front_image_url": book.front_image_url,
            "front_image_presigned_url": front_presigned_url,
            "back_image_url": book.back_image_url,
            "back_image_presigned_url": back_presigned_url,
            "page_1_image_url": book.page_1_image_url,
            "page_1_image_presigned_url": page_1_presigned_url,
            "page_2_image_url": book.page_2_image_url,
            "page_2_image_presigned_url": page_2_presigned_url,
            "page_3_image_url": book.page_3_image_url,
            "page_3_image_presigned_url": page_3_presigned_url,
            "page_4_image_url": book.page_4_image_url,
            "page_4_image_presigned_url": page_4_presigned_url,
            "book_url": book.book_url if include_pdf_url else None,
            "total_pages": book.total_pages,
            "book_type_id": book.book_type_id,
            "theme_id": book.theme_id,
            "language_id": book.language_id,
            "book_type": normalized_response_book_type,
            "style": style,
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
            "age": book.age_label or (getattr(book.age_group, "value", None) if book.age_group else None),
            "age_group": book.age_label or (getattr(book.age_group, "value", None) if book.age_group else None),
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

    async def _get_category_row(self, category_id: int | None) -> BookCategory | None:
        if category_id is None:
            return None
        result = await self.db.execute(
            select(BookCategory).where(BookCategory.category_id == category_id)
        )
        return result.scalar_one_or_none()

    async def _validate_book_category_placement(
        self,
        *,
        category_row: BookCategory | None,
        category_id: int | None,
        is_personalized: bool,
    ) -> None:
        if category_id is None:
            raise BadRequestException("category_id is required")

        if category_row is None:
            raise BadRequestException("Category not found")

        if bool(category_row.personalized) == bool(is_personalized):
            return

        if is_personalized:
            raise BadRequestException(
                "Personalized books can only be stored in personalized story/coloring categories"
            )

        raise BadRequestException(
            "Digital books can only be stored in non-personalized categories"
        )

    async def _get_attribute_option_value(self, option_id: int | None) -> str | None:
        if option_id is None:
            return None
        result = await self.db.execute(
            select(BookAttributeOption.value).where(BookAttributeOption.id == option_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _infer_personalized_kind(
        *,
        book_type: str | None,
        category_name: str | None,
    ) -> str | None:
        source = f"{book_type or ''} {category_name or ''}".strip().lower()
        if not source:
            return None
        if "color" in source:
            return "coloring"
        if "story" in source or "tale" in source:
            return "story"
        return None

    async def _presign_url(self, object_name: str | None, _book_id: int, _image_kind: str) -> str | None:
        if not object_name:
            return None

        raw = str(object_name).strip()
        if raw.startswith("http://") or raw.startswith("https://"):
            return raw

        # Always serve through API proxy so browser access is stable across
        # environments even when direct MinIO/public URLs are misconfigured.
        object_path = raw.lstrip("/")
        return f"/api/v1/digital-books/images/{object_path}"

    async def _presign_category_image_url(
        self,
        object_name: str | None,
        _category_id: int,
    ) -> str | None:
        if not object_name:
            return None

        raw = str(object_name).strip()
        if raw.startswith("http://") or raw.startswith("https://"):
            return raw

        # Always serve through API proxy so browser access is stable across
        # environments even when direct MinIO/public URLs are misconfigured.
        object_path = raw.lstrip("/")
        return f"/api/v1/digital-books/images/{object_path}"

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
        # Digital story books and digital coloring books are taxed at 5% GST.
        _ = book
        return GST_RATE_DIGITAL_PERCENT

