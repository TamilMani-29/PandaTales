"""Generation Configuration API Routes (Admin & Public)"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import (
    PaginationParams,
    get_logger,
    paginated_response,
    success_response,
)
from app.db.session import get_db
from app.schemas.generation_config import (
    GenerationConfigCreate,
    GenerationConfigFilters,
    GenerationConfigListItem,
    GenerationConfigResponse,
    GenerationConfigUpdate,
    PublicThemeItem,
    ThemeCreate,
    ThemeUpdate,
)
from app.services.generation_config import GenerationConfigService

logger = get_logger(__name__)

router = APIRouter()

# Public router for themes (no admin required)
public_router = APIRouter(prefix="/themes", tags=["Themes"])

# Admin router for configurations (requires admin auth)
admin_router = APIRouter(prefix="/admin/configs", tags=["Admin - Generation Configs"])


# ============================================================================
# PUBLIC API - Available to all users
# ============================================================================


@public_router.get(
    "",
    response_model=list[PublicThemeItem],
    status_code=status.HTTP_200_OK,
    summary="Get active themes",
    description="Get list of active themes available for theme-based coloring book generation",
)
async def get_active_themes(
    db: AsyncSession = Depends(get_db),
) -> list[PublicThemeItem]:
    """Get active themes for user selection"""
    service = GenerationConfigService(db)
    themes = await service.get_active_themes()
    return themes


# ============================================================================
# ADMIN API - Requires admin authentication
# ============================================================================


@admin_router.get(
    "",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="List generation configs",
    description="Get paginated list of generation configurations with filters (Admin only)",
)
async def list_generation_configs(
    # Pagination
    pagination: PaginationParams = Depends(),
    # Filters
    config_type: str | None = Query(None, description="Filter by config type"),
    category: str | None = Query(None, description="Filter by category"),
    applies_to: str | None = Query(None, description="Filter by applies_to"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    is_premium: bool | None = Query(None, description="Filter by premium status"),
    search: str | None = Query(
        None, max_length=100, description="Search in name/display_name/description"
    ),
    sort_by: str = Query("sort_order", description="Sort field"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    # Dependencies
    db: AsyncSession = Depends(get_db),
    # TODO: Add admin authentication dependency
    # current_admin: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """List generation configs with pagination and filters (Admin only)"""

    # Build filters
    filters = GenerationConfigFilters(
        config_type=config_type,
        category=category,
        applies_to=applies_to,
        is_active=is_active,
        is_premium=is_premium,
        search=search,
    )

    service = GenerationConfigService(db)

    # Get configs
    configs, total = await service.list_configs(
        filters=filters,
        page=pagination.page,
        page_size=pagination.page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return paginated_response(
        items=[GenerationConfigListItem.model_validate(config) for config in configs],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@admin_router.post(
    "",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create generation config",
    description="Create a new generation configuration (Admin only)",
)
async def create_generation_config(
    data: GenerationConfigCreate,
    db: AsyncSession = Depends(get_db),
    # TODO: Add admin authentication dependency
    # current_admin: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Create a new generation config (Admin only)"""
    service = GenerationConfigService(db)
    config = await service.create_config(data)

    logger.info(f"Admin created generation config: {config.id}")

    return success_response(
        data=GenerationConfigResponse.model_validate(config),
        message="Generation config created successfully",
    )


@admin_router.get(
    "/{config_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get generation config",
    description="Get generation config by ID (Admin only)",
)
async def get_generation_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    # TODO: Add admin authentication dependency
    # current_admin: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Get generation config by ID (Admin only)"""
    service = GenerationConfigService(db)
    config = await service.get_config(config_id)

    return success_response(
        data=GenerationConfigResponse.model_validate(config),
        message="Generation config retrieved successfully",
    )


@admin_router.patch(
    "/{config_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Update generation config",
    description="Update generation config (Admin only)",
)
async def update_generation_config(
    config_id: UUID,
    data: GenerationConfigUpdate,
    db: AsyncSession = Depends(get_db),
    # TODO: Add admin authentication dependency
    # current_admin: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Update generation config (Admin only)"""
    service = GenerationConfigService(db)
    config = await service.update_config(config_id, data)

    logger.info(f"Admin updated generation config: {config_id}")

    return success_response(
        data=GenerationConfigResponse.model_validate(config),
        message="Generation config updated successfully",
    )


@admin_router.delete(
    "/{config_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Delete generation config",
    description="Delete generation config (Admin only)",
)
async def delete_generation_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    # TODO: Add admin authentication dependency
    # current_admin: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Delete generation config (Admin only)"""
    service = GenerationConfigService(db)
    await service.delete_config(config_id)

    logger.info(f"Admin deleted generation config: {config_id}")

    return success_response(
        data=None,
        message="Generation config deleted successfully",
    )


# ============================================================================
# ADMIN API - Theme Shortcuts
# ============================================================================


@admin_router.post(
    "/themes",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create theme (simplified)",
    description="Create a new theme using simplified schema (Admin only)",
)
async def create_theme(
    data: ThemeCreate,
    db: AsyncSession = Depends(get_db),
    # TODO: Add admin authentication dependency
    # current_admin: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Create a new theme (simplified helper) (Admin only)"""
    service = GenerationConfigService(db)
    theme = await service.create_theme(data)

    logger.info(f"Admin created theme: {theme.id}")

    return success_response(
        data=GenerationConfigResponse.model_validate(theme),
        message="Theme created successfully",
    )


@admin_router.patch(
    "/themes/{theme_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Update theme (simplified)",
    description="Update theme using simplified schema (Admin only)",
)
async def update_theme(
    theme_id: UUID,
    data: ThemeUpdate,
    db: AsyncSession = Depends(get_db),
    # TODO: Add admin authentication dependency
    # current_admin: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Update theme (simplified helper) (Admin only)"""
    service = GenerationConfigService(db)
    theme = await service.update_theme(theme_id, data)

    logger.info(f"Admin updated theme: {theme_id}")

    return success_response(
        data=GenerationConfigResponse.model_validate(theme),
        message="Theme updated successfully",
    )
