"""Coloring Book Template API Routes"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import PaginationParams, get_logger, paginated_response, success_response
from app.db.session import get_db
from app.schemas.coloring_book_template import (
    ColoringBookTemplateCreate,
    ColoringBookTemplateFilters,
    ColoringBookTemplateListItem,
    ColoringBookTemplateResponse,
    ColoringBookTemplateUpdate,
)
from app.services.coloring_book_template import ColoringBookTemplateService

logger = get_logger(__name__)

router = APIRouter(prefix="/coloring-books", tags=["Coloring Book Templates"])


@router.get(
    "",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="List coloring book templates",
    description="Get a paginated list of coloring book templates with optional filters",
)
async def list_coloring_book_templates(
    # Pagination
    pagination: PaginationParams = Depends(),
    # Filters
    theme: str | None = Query(None, description="Filter by theme"),
    age_group: str | None = Query(None, description="Filter by age group"),
    min_price: float | None = Query(None, ge=0, description="Minimum price"),
    max_price: float | None = Query(None, ge=0, description="Maximum price"),
    search: str | None = Query(
        None, max_length=100, description="Search in title/description"
    ),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    # Dependencies
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List coloring book templates with pagination and filters"""

    # Build filters
    filters = ColoringBookTemplateFilters(
        theme=theme,
        age_group=age_group,
        min_price=min_price,
        max_price=max_price,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    service = ColoringBookTemplateService(db)
    result = await service.list_templates(
        filters=filters,
        page=pagination.page,
        limit=pagination.limit,
    )

    # Convert to list items
    items = [ColoringBookTemplateListItem.model_validate(item) for item in result.items]

    return paginated_response(
        data=[item.model_dump() for item in items],
        page=result.page,
        limit=result.limit,
        total=result.total,
        message="Coloring book templates retrieved successfully",
    )


@router.get(
    "/{template_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get coloring book template details",
    description="Get detailed information about a specific coloring book template",
)
async def get_coloring_book_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get a single coloring book template by ID"""

    service = ColoringBookTemplateService(db)
    template = await service.get_template(template_id)

    response_data = ColoringBookTemplateResponse.model_validate(template)

    return success_response(
        data=response_data.model_dump(),
        message="Coloring book template retrieved successfully",
    )


@router.post(
    "",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create coloring book template",
    description="Create a new coloring book template (Admin only)",
)
async def create_coloring_book_template(
    template_data: ColoringBookTemplateCreate,
    db: AsyncSession = Depends(get_db),
    # TODO: Add auth dependency - current_user: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Create a new coloring book template"""

    service = ColoringBookTemplateService(db)
    template = await service.create_template(template_data)

    response_data = ColoringBookTemplateResponse.model_validate(template)

    return success_response(
        data=response_data.model_dump(),
        message="Coloring book template created successfully",
    )


@router.patch(
    "/{template_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Update coloring book template",
    description="Update an existing coloring book template (Admin only)",
)
async def update_coloring_book_template(
    template_id: UUID,
    template_data: ColoringBookTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    # TODO: Add auth dependency - current_user: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Update a coloring book template"""

    service = ColoringBookTemplateService(db)
    template = await service.update_template(template_id, template_data)

    response_data = ColoringBookTemplateResponse.model_validate(template)

    return success_response(
        data=response_data.model_dump(),
        message="Coloring book template updated successfully",
    )


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete coloring book template",
    description="Soft delete a coloring book template (Admin only)",
)
async def delete_coloring_book_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    # TODO: Add auth dependency - current_user: User = Depends(get_current_admin_user),
) -> None:
    """Delete a coloring book template"""

    service = ColoringBookTemplateService(db)
    await service.delete_template(template_id)


@router.get(
    "/themes/list",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="List all themes",
    description="Get a list of all available coloring book themes",
)
async def list_coloring_book_themes(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get all themes"""

    service = ColoringBookTemplateService(db)
    themes = await service.get_all_themes()

    return success_response(
        data={"themes": themes},
        message="Themes retrieved successfully",
    )
