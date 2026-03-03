"""Generation Configuration Service"""

from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.common.logging import get_logger
from app.common.pagination import PaginationParams
from app.models.generation_config import GenerationConfig
from app.repositories.generation_config import GenerationConfigRepository
from app.schemas.generation_config import (
    GenerationConfigCreate,
    GenerationConfigFilters,
    GenerationConfigListItem,
    GenerationConfigResponse,
    GenerationConfigUpdate,
    PublicThemeItem,
    ThemeConfigData,
    ThemeCreate,
    ThemeUpdate,
)

logger = get_logger(__name__)


class GenerationConfigService:
    """Service for generation configuration management"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = GenerationConfigRepository(db)

    async def list_configs(
        self,
        filters: GenerationConfigFilters | None = None,
        pagination: PaginationParams | None = None,
    ) -> tuple[Sequence[GenerationConfigListItem], int]:
        """List generation configurations"""
        logger.info("listing_generation_configs", filters=filters)
        configs, total = await self.repository.get_all(filters, pagination)
        logger.info("generation_configs_listed", total=total)

        items = [
            GenerationConfigListItem(
                id=config.id,
                config_type=config.config_type,
                name=config.name,
                display_name=config.display_name,
                description=config.description,
                icon_url=config.icon_url,
                preview_image_url=config.preview_image_url,
                category=config.category,
                tags=config.tags,
                applies_to=config.applies_to,
                is_active=config.is_active,
                is_premium=config.is_premium,
                is_default=config.is_default,
                usage_count=config.usage_count,
                sort_order=config.sort_order,
            )
            for config in configs
        ]

        return items, total

    async def get_config(self, config_id: UUID) -> GenerationConfigResponse:
        """Get configuration details"""
        logger.info("fetching_generation_config", config_id=str(config_id))
        config = await self.repository.get_by_id(config_id)
        if not config:
            logger.warning("generation_config_not_found", config_id=str(config_id))
            raise NotFoundException("Configuration not found")

        return GenerationConfigResponse.model_validate(config)

    async def create_config(
        self, data: GenerationConfigCreate
    ) -> GenerationConfigResponse:
        """Create a new configuration"""
        logger.info("creating_generation_config", name=data.name, config_type=data.config_type)
        
        # Check for duplicate name within same type
        existing = await self.repository.get_by_name(data.name, data.config_type)
        if existing:
            logger.warning("generation_config_duplicate", name=data.name, config_type=data.config_type)
            raise ConflictException(f"Configuration with name '{data.name}' already exists")

        # Validate photo range
        if data.min_photos > data.max_photos:
            raise ValueError("min_photos cannot be greater than max_photos")

        config = GenerationConfig(
            config_type=data.config_type,
            name=data.name,
            display_name=data.display_name,
            description=data.description,
            icon_url=data.icon_url,
            preview_image_url=data.preview_image_url,
            config_data=data.config_data,
            category=data.category,
            tags=data.tags,
            applies_to=data.applies_to,
            max_photos=data.max_photos,
            min_photos=data.min_photos,
            is_active=data.is_active,
            is_premium=data.is_premium,
            is_default=data.is_default,
            sort_order=data.sort_order,
        )

        config = await self.repository.create(config)

        # If set as default, ensure no other config of same type is default
        if data.is_default:
            await self.repository.set_as_default(config.id, config.config_type)

        await self.db.commit()

        return GenerationConfigResponse.model_validate(config)

    async def update_config(
        self, config_id: UUID, data: GenerationConfigUpdate
    ) -> GenerationConfigResponse:
        """Update a configuration"""
        config = await self.repository.get_by_id(config_id)
        if not config:
            raise NotFoundException("Configuration not found")

        # Update fields
        if data.display_name is not None:
            config.display_name = data.display_name
        if data.description is not None:
            config.description = data.description
        if data.icon_url is not None:
            config.icon_url = data.icon_url
        if data.preview_image_url is not None:
            config.preview_image_url = data.preview_image_url
        if data.config_data is not None:
            config.config_data = data.config_data
        if data.category is not None:
            config.category = data.category
        if data.tags is not None:
            config.tags = data.tags
        if data.applies_to is not None:
            config.applies_to = data.applies_to
        if data.max_photos is not None:
            config.max_photos = data.max_photos
        if data.min_photos is not None:
            config.min_photos = data.min_photos
        if data.is_active is not None:
            config.is_active = data.is_active
        if data.is_premium is not None:
            config.is_premium = data.is_premium
        if data.is_default is not None:
            config.is_default = data.is_default
        if data.sort_order is not None:
            config.sort_order = data.sort_order

        # Validate photo range
        if config.min_photos > config.max_photos:
            raise ValueError("min_photos cannot be greater than max_photos")

        config = await self.repository.update(config)

        # Handle default flag
        if data.is_default and config.is_default:
            await self.repository.set_as_default(config_id, config.config_type)

        await self.db.commit()

        return GenerationConfigResponse.model_validate(config)

    async def delete_config(self, config_id: UUID) -> None:
        """Delete a configuration"""
        config = await self.repository.get_by_id(config_id)
        if not config:
            raise NotFoundException("Configuration not found")

        # Don't allow deleting default configs
        if config.is_default:
            raise ForbiddenException("Cannot delete default configuration")

        await self.repository.delete(config)
        await self.db.commit()

    async def get_active_themes(
        self, applies_to: str = "coloring_book", include_premium: bool = True
    ) -> Sequence[PublicThemeItem]:
        """Get active themes for user selection"""
        is_premium = None if include_premium else False
        themes = await self.repository.get_active_themes(applies_to, is_premium)

        return [
            PublicThemeItem(
                id=theme.id,
                name=theme.name,
                display_name=theme.display_name,
                description=theme.description,
                icon_url=theme.icon_url,
                preview_image_url=theme.preview_image_url,
                category=theme.category,
                tags=theme.tags,
                is_premium=theme.is_premium,
                is_default=theme.is_default,
                min_photos=theme.min_photos,
                max_photos=theme.max_photos,
            )
            for theme in themes
        ]

    # Simplified theme management methods
    async def create_theme(self, data: ThemeCreate) -> GenerationConfigResponse:
        """Simplified theme creation"""
        # Build config_data from theme-specific fields
        config_data = {
            "base_prompt": data.base_prompt,
            "style_parameters": data.style_parameters,
            "sample_keywords": data.sample_keywords,
            "generation_settings": data.generation_settings,
        }

        config_create = GenerationConfigCreate(
            config_type="theme",
            name=data.name,
            display_name=data.display_name,
            description=data.description,
            icon_url=data.icon_url,
            preview_image_url=data.preview_image_url,
            config_data=config_data,
            category=data.category,
            tags=data.tags,
            applies_to="coloring_book",
            max_photos=data.max_photos,
            min_photos=data.min_photos,
            is_active=True,
            is_premium=data.is_premium,
            is_default=False,
            sort_order=0,
        )

        return await self.create_config(config_create)

    async def update_theme(
        self, theme_id: UUID, data: ThemeUpdate
    ) -> GenerationConfigResponse:
        """Simplified theme update"""
        theme = await self.repository.get_by_id(theme_id)
        if not theme or theme.config_type != "theme":
            raise NotFoundException("Theme not found")

        # Update config_data if theme-specific fields are provided
        config_data = theme.config_data.copy() if theme.config_data else {}

        if data.base_prompt is not None:
            config_data["base_prompt"] = data.base_prompt
        if data.style_parameters is not None:
            config_data["style_parameters"] = data.style_parameters
        if data.sample_keywords is not None:
            config_data["sample_keywords"] = data.sample_keywords
        if data.generation_settings is not None:
            config_data["generation_settings"] = data.generation_settings

        config_update = GenerationConfigUpdate(
            display_name=data.display_name,
            description=data.description,
            icon_url=data.icon_url,
            preview_image_url=data.preview_image_url,
            config_data=config_data if any([
                data.base_prompt,
                data.style_parameters,
                data.sample_keywords,
                data.generation_settings,
            ]) else None,
            category=data.category,
            tags=data.tags,
            max_photos=data.max_photos,
            min_photos=data.min_photos,
            is_active=data.is_active,
            is_premium=data.is_premium,
            is_default=data.is_default,
            sort_order=data.sort_order,
        )

        return await self.update_config(theme_id, config_update)
