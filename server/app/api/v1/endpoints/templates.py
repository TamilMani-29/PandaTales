"""Book Template API Routes"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import PaginationParams, get_logger, paginated_response, success_response
from app.db.session import get_db
from app.schemas.book_template import (
    BookTemplateCreate,
    BookTemplateFilters,
    BookTemplateListItem,
    BookTemplateResponse,
    BookTemplateUpdate,
)
from app.services.book_template import BookTemplateService

logger = get_logger(__name__)

router = APIRouter(prefix="/templates", tags=["Book Templates"])


@router.get(
    "",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="List book templates",
    description="Get a paginated list of book templates with optional filters",
)
async def list_templates(
    # Pagination
    pagination: PaginationParams = Depends(),
    # Filters
    template_type: str | None = Query(None, description="Filter by template type"),
    genre: str | None = Query(None, description="Filter by genre"),
    age_group: str | None = Query(None, description="Filter by age group"),
    difficulty: str | None = Query(None, description="Filter by difficulty"),
    min_price: float | None = Query(None, ge=0, description="Minimum price"),
    max_price: float | None = Query(None, ge=0, description="Maximum price"),
    search: str | None = Query(None, max_length=100, description="Search in title/description"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    # Dependencies
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List templates with pagination and filters"""

    # Build filters
    filters = BookTemplateFilters(
        template_type=template_type,
        genre=genre,
        age_group=age_group,
        difficulty=difficulty,
        min_price=min_price,
        max_price=max_price,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    service = BookTemplateService(db)
    result = await service.list_templates(
        filters=filters,
        page=pagination.page,
        limit=pagination.limit,
    )

    # Convert to list items
    items = [BookTemplateListItem.model_validate(item) for item in result.items]

    return paginated_response(
        data=[item.model_dump() for item in items],
        page=result.page,
        limit=result.limit,
        total=result.total,
        message="Templates retrieved successfully",
    )


@router.get(
    "/{template_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get template details",
    description="Get detailed information about a specific book template",
)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get a single template by ID"""

    service = BookTemplateService(db)
    template = await service.get_template(template_id)

    response_data = BookTemplateResponse.model_validate(template)

    return success_response(
        data=response_data.model_dump(),
        message="Template retrieved successfully",
    )


@router.post(
    "",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create book template",
    description="Create a new book template (Admin only)",
)
async def create_template(
    template_data: BookTemplateCreate,
    db: AsyncSession = Depends(get_db),
    # TODO: Add auth dependency - current_user: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Create a new template"""

    service = BookTemplateService(db)
    template = await service.create_template(template_data)

    response_data = BookTemplateResponse.model_validate(template)

    return success_response(
        data=response_data.model_dump(),
        message="Template created successfully",
    )


@router.patch(
    "/{template_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Update book template",
    description="Update an existing book template (Admin only)",
)
async def update_template(
    template_id: UUID,
    template_data: BookTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    # TODO: Add auth dependency - current_user: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Update a template"""

    service = BookTemplateService(db)
    template = await service.update_template(template_id, template_data)

    response_data = BookTemplateResponse.model_validate(template)

    return success_response(
        data=response_data.model_dump(),
        message="Template updated successfully",
    )


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete book template",
    description="Soft delete a book template (Admin only)",
)
async def delete_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    # TODO: Add auth dependency - current_user: User = Depends(get_current_admin_user),
) -> None:
    """Delete a template"""

    service = BookTemplateService(db)
    await service.delete_template(template_id)


@router.get(
    "/genres/list",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="List all genres",
    description="Get a list of all available template genres",
)
async def list_genres(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get all genres"""

    service = BookTemplateService(db)
    genres = await service.get_all_genres()

    return success_response(
        data={"genres": genres},
        message="Genres retrieved successfully",
    )


@router.get(
    "/series/{series_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get series templates",
    description="Get all templates in a series",
)
async def get_series_templates(
    series_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get all templates in a series"""

    service = BookTemplateService(db)
    series_info = await service.get_series_info(series_id)

    if not series_info:
        return success_response(
            data={"books": []},
            message="No templates found in this series",
        )

    return success_response(
        data=series_info.model_dump(),
        message="Series templates retrieved successfully",
    )
