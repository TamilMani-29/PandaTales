"""Generated Book Repository"""

from datetime import datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.pagination import PaginationParams
from app.models.generated_book import GeneratedBook
from app.schemas.generated_book import GeneratedBookFilters


class GeneratedBookRepository:
    """Repository for generated book database operations"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(
        self, book_id: UUID, user_id: UUID | None = None
    ) -> GeneratedBook | None:
        """Get a generated book by ID"""
        query = select(GeneratedBook).where(GeneratedBook.id == book_id)

        if user_id:
            query = query.where(GeneratedBook.user_id == user_id)

        # Eager load relationships
        query = query.options(
            selectinload(GeneratedBook.user),
            selectinload(GeneratedBook.child),
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        user_id: UUID,
        filters: GeneratedBookFilters | None = None,
        pagination: PaginationParams | None = None,
    ) -> tuple[Sequence[GeneratedBook], int]:
        """Get all generated books for a user with filters and pagination"""
        # Base query
        query = select(GeneratedBook).where(GeneratedBook.user_id == user_id)

        # Apply filters
        if filters:
            if filters.child_id:
                query = query.where(GeneratedBook.child_id == filters.child_id)

            if filters.template_type:
                query = query.where(GeneratedBook.template_type == filters.template_type)

            if filters.status:
                query = query.where(GeneratedBook.status == filters.status)

            if filters.is_purchased is not None:
                query = query.where(GeneratedBook.is_purchased == filters.is_purchased)

            # Apply sorting
            if filters.sort == "newest":
                query = query.order_by(desc(GeneratedBook.created_at))
            elif filters.sort == "oldest":
                query = query.order_by(GeneratedBook.created_at)
            # Note: "title" sort would require joining with template tables
        else:
            # Default sort
            query = query.order_by(desc(GeneratedBook.created_at))

        # Eager load relationships
        query = query.options(
            selectinload(GeneratedBook.user),
            selectinload(GeneratedBook.child),
        )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        if pagination:
            query = query.offset(pagination.offset).limit(pagination.page_size)

        result = await self.db.execute(query)
        books = result.scalars().all()

        return books, total

    async def create(self, book: GeneratedBook) -> GeneratedBook:
        """Create a new generated book"""
        self.db.add(book)
        await self.db.flush()
        await self.db.refresh(book)
        return book

    async def update(self, book: GeneratedBook) -> GeneratedBook:
        """Update a generated book"""
        await self.db.flush()
        await self.db.refresh(book)
        return book

    async def delete(self, book: GeneratedBook) -> None:
        """Delete a generated book"""
        await self.db.delete(book)
        await self.db.flush()

    async def get_by_status(
        self, status: str, limit: int | None = None
    ) -> Sequence[GeneratedBook]:
        """Get books by status (useful for processing queues)"""
        query = select(GeneratedBook).where(GeneratedBook.status == status)
        query = query.order_by(GeneratedBook.created_at)

        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_queued_position(self, book_id: UUID) -> int:
        """Get the queue position of a book"""
        book = await self.get_by_id(book_id)
        if not book or book.status != "queued":
            return 0

        # Count how many books are ahead in the queue
        query = select(func.count()).where(
            and_(
                GeneratedBook.status == "queued",
                GeneratedBook.created_at < book.created_at,
            )
        )

        result = await self.db.execute(query)
        position = result.scalar_one()
        return position + 1  # Position is 1-indexed

    async def update_status(
        self,
        book_id: UUID,
        status: str,
        progress: int = 0,
        current_step: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        error_details: str | None = None,
    ) -> GeneratedBook | None:
        """Update book generation status"""
        book = await self.get_by_id(book_id)
        if not book:
            return None

        book.status = status
        book.progress = progress

        if current_step:
            book.current_step = current_step

        if status == "completed":
            book.completed_at = datetime.utcnow()
            book.progress = 100
            if book.created_at:
                duration = (datetime.utcnow() - book.created_at).total_seconds()
                book.generation_duration = int(duration)

        elif status == "failed":
            book.failed_at = datetime.utcnow()
            book.error_code = error_code
            book.error_message = error_message
            book.error_details = error_details

        await self.db.flush()
        await self.db.refresh(book)
        return book

    async def get_user_generation_count_today(self, user_id: UUID) -> int:
        """Get count of books generated by user today (for rate limiting)"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        query = select(func.count()).where(
            and_(
                GeneratedBook.user_id == user_id,
                GeneratedBook.created_at >= today_start,
            )
        )

        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_pending_generations(self, user_id: UUID) -> Sequence[GeneratedBook]:
        """Get all pending (queued or processing) generations for a user"""
        query = select(GeneratedBook).where(
            and_(
                GeneratedBook.user_id == user_id,
                or_(
                    GeneratedBook.status == "queued",
                    GeneratedBook.status == "processing",
                ),
            )
        )
        query = query.order_by(GeneratedBook.created_at)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def mark_as_purchased(
        self, book_id: UUID, user_id: UUID
    ) -> GeneratedBook | None:
        """Mark a book as purchased"""
        book = await self.get_by_id(book_id, user_id)
        if not book:
            return None

        book.is_purchased = True
        book.purchased_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(book)
        return book

    async def get_by_id_direct(self, book_id: UUID) -> GeneratedBook | None:
        """Get a generated book by ID without user filtering (for background workers)"""
        query = select(GeneratedBook).where(GeneratedBook.id == book_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_fields(
        self,
        book_id: UUID,
        **fields,
    ) -> GeneratedBook | None:
        """Update specific fields of a generated book"""
        book = await self.get_by_id_direct(book_id)
        if not book:
            return None

        # Update only provided fields
        for key, value in fields.items():
            if hasattr(book, key):
                setattr(book, key, value)

        await self.db.flush()
        await self.db.refresh(book)
        return book
