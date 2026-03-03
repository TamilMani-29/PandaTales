"""Story Book Template API Routes"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import PaginationParams, get_logger, paginated_response, success_response
from app.db.session import get_db
from app.schemas.story_book_template import (
    StoryBookTemplateCreate,
    StoryBookTemplateFilters,
    StoryBookTemplateListItem,
    StoryBookTemplateResponse,
    StoryBookTemplateUpdate,
)
from app.services.story_book_template import StoryBookTemplateService

logger = get_logger(__name__)

router = APIRouter(prefix="/story-books", tags=["Story Book Templates"])


@router.get(
    "",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="List story book templates",
    description="Get a paginated list of story book templates with optional filters",
)
async def list_story_book_templates(
    # Pagination
    pagination: PaginationParams = Depends(),
    # Filters
    genre: str | None = Query(None, description="Filter by genre"),
    age_group: str | None = Query(None, description="Filter by age group"),
    reading_level: str | None = Query(None, description="Filter by reading level"),
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
    """List story book templates with pagination and filters"""

    # Build filters
    filters = StoryBookTemplateFilters(
        genre=genre,
        age_group=age_group,
        reading_level=reading_level,
        min_price=min_price,
        max_price=max_price,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    service = StoryBookTemplateService(db)
    result = await service.list_templates(
        filters=filters,
        page=pagination.page,
        limit=pagination.limit,
    )

    # Convert to list items
    items = [StoryBookTemplateListItem.model_validate(item) for item in result.items]

    return paginated_response(
        data=[item.model_dump() for item in items],
        page=result.page,
        limit=result.limit,
        total=result.total,
        message="Story book templates retrieved successfully",
    )


@router.get(
    "/{template_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get story book template details",
    description="Get detailed information about a specific story book template",
)
async def get_story_book_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get a single story book template by ID"""

    service = StoryBookTemplateService(db)
    template = await service.get_template(template_id)

    response_data = StoryBookTemplateResponse.model_validate(template)

    return success_response(
        data=response_data.model_dump(),
        message="Story book template retrieved successfully",
    )


@router.post(
    "",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create story book template",
    description="Create a new story book template (Admin only)",
)
async def create_story_book_template(
    template_data: StoryBookTemplateCreate,
    db: AsyncSession = Depends(get_db),
    # TODO: Add auth dependency - current_user: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Create a new story book template"""

    service = StoryBookTemplateService(db)
    template = await service.create_template(template_data)

    response_data = StoryBookTemplateResponse.model_validate(template)

    return success_response(
        data=response_data.model_dump(),
        message="Story book template created successfully",
    )


@router.patch(
    "/{template_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Update story book template",
    description="Update an existing story book template (Admin only)",
)
async def update_story_book_template(
    template_id: UUID,
    template_data: StoryBookTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    # TODO: Add auth dependency - current_user: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Update a story book template"""

    service = StoryBookTemplateService(db)
    template = await service.update_template(template_id, template_data)

    response_data = StoryBookTemplateResponse.model_validate(template)

    return success_response(
        data=response_data.model_dump(),
        message="Story book template updated successfully",
    )


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete story book template",
    description="Soft delete a story book template (Admin only)",
)
async def delete_story_book_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    # TODO: Add auth dependency - current_user: User = Depends(get_current_admin_user),
) -> None:
    """Delete a story book template"""

    service = StoryBookTemplateService(db)
    await service.delete_template(template_id)


@router.get(
    "/genres/list",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="List all genres",
    description="Get a list of all available story book genres",
)
async def list_story_book_genres(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get all genres"""

    service = StoryBookTemplateService(db)
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
    description="Get all story book templates in a series",
)
async def get_series_story_book_templates(
    series_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get all story book templates in a series"""

    service = StoryBookTemplateService(db)
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
