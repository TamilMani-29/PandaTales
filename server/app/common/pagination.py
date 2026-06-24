"""Pagination Utilities"""

from typing import Any, Generic, Sequence, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination query parameters"""

    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset from page and limit"""
        return (self.page - 1) * self.limit


class Paginated(BaseModel, Generic[T]):
    """Paginated result container"""

    items: Sequence[T]
    page: int
    limit: int
    total: int
    pages: int

    model_config = {"arbitrary_types_allowed": True}


async def paginate(
    db: AsyncSession,
    query: Select[tuple[T]],
    page: int = 1,
    limit: int = 20,
) -> Paginated[T]:
    """
    Paginate a SQLAlchemy query
    
    Args:
        db: Database session
        query: SQLAlchemy select query
        page: Page number (1-indexed)
        limit: Items per page
        
    Returns:
        Paginated result with items and metadata
    """
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated items
    offset = (page - 1) * limit
    paginated_query = query.offset(offset).limit(limit)
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    # Calculate total pages
    pages = (total + limit - 1) // limit if total > 0 else 0

    return Paginated(
        items=items,
        page=page,
        limit=limit,
        total=total,
        pages=pages,
    )
