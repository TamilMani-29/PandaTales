"""Generation Configuration Repository"""

from typing import Sequence
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginationParams
from app.models.generation_config import GenerationConfig
from app.schemas.generation_config import GenerationConfigFilters


class GenerationConfigRepository:
    """Repository for generation configuration database operations"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, config_id: UUID) -> GenerationConfig | None:
        """Get a configuration by ID"""
        query = select(GenerationConfig).where(GenerationConfig.id == config_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str, config_type: str) -> GenerationConfig | None:
        """Get a configuration by name and type"""
        query = select(GenerationConfig).where(
            and_(
                GenerationConfig.name == name,
                GenerationConfig.config_type == config_type,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        filters: GenerationConfigFilters | None = None,
        pagination: PaginationParams | None = None,
    ) -> tuple[Sequence[GenerationConfig], int]:
        """Get all configurations with filters and pagination"""
        # Base query
        query = select(GenerationConfig)

        # Apply filters
        if filters:
            if filters.config_type:
                query = query.where(GenerationConfig.config_type == filters.config_type)

            if filters.category:
                query = query.where(GenerationConfig.category == filters.category)

            if filters.applies_to:
                query = query.where(
                    or_(
                        GenerationConfig.applies_to == filters.applies_to,
                        GenerationConfig.applies_to == "both",
                    )
                )

            if filters.is_active is not None:
                query = query.where(GenerationConfig.is_active == filters.is_active)

            if filters.is_premium is not None:
                query = query.where(GenerationConfig.is_premium == filters.is_premium)

            if filters.search:
                search_pattern = f"%{filters.search}%"
                query = query.where(
                    or_(
                        GenerationConfig.name.ilike(search_pattern),
                        GenerationConfig.display_name.ilike(search_pattern),
                        GenerationConfig.description.ilike(search_pattern),
                    )
                )

            # Apply sorting
            if filters.sort == "name":
                query = query.order_by(GenerationConfig.display_name)
            elif filters.sort == "usage":
                query = query.order_by(desc(GenerationConfig.usage_count))
            elif filters.sort == "recent":
                query = query.order_by(desc(GenerationConfig.created_at))
            else:  # sort_order
                query = query.order_by(
                    GenerationConfig.sort_order, GenerationConfig.display_name
                )
        else:
            # Default sort
            query = query.order_by(
                GenerationConfig.sort_order, GenerationConfig.display_name
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        if pagination:
            query = query.offset(pagination.offset).limit(pagination.page_size)

        result = await self.db.execute(query)
        configs = result.scalars().all()

        return configs, total

    async def create(self, config: GenerationConfig) -> GenerationConfig:
        """Create a new configuration"""
        self.db.add(config)
        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def update(self, config: GenerationConfig) -> GenerationConfig:
        """Update a configuration"""
        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def delete(self, config: GenerationConfig) -> None:
        """Delete a configuration"""
        await self.db.delete(config)
        await self.db.flush()

    async def increment_usage(self, config_id: UUID) -> None:
        """Increment usage count for a configuration"""
        config = await self.get_by_id(config_id)
        if config:
            config.usage_count += 1
            await self.db.flush()

    async def get_active_themes(
        self, applies_to: str = "coloring_book", is_premium: bool | None = None
    ) -> Sequence[GenerationConfig]:
        """Get active themes for user selection"""
        query = select(GenerationConfig).where(
            and_(
                GenerationConfig.config_type == "theme",
                GenerationConfig.is_active == True,
                or_(
                    GenerationConfig.applies_to == applies_to,
                    GenerationConfig.applies_to == "both",
                ),
            )
        )

        if is_premium is not None:
            query = query.where(GenerationConfig.is_premium == is_premium)

        query = query.order_by(
            GenerationConfig.sort_order, GenerationConfig.display_name
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_default_config(
        self, config_type: str, applies_to: str = "coloring_book"
    ) -> GenerationConfig | None:
        """Get the default configuration for a type"""
        query = select(GenerationConfig).where(
            and_(
                GenerationConfig.config_type == config_type,
                GenerationConfig.is_default == True,
                GenerationConfig.is_active == True,
                or_(
                    GenerationConfig.applies_to == applies_to,
                    GenerationConfig.applies_to == "both",
                ),
            )
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def set_as_default(
        self, config_id: UUID, config_type: str
    ) -> GenerationConfig | None:
        """Set a configuration as the default (unsets others of same type)"""
        config = await self.get_by_id(config_id)
        if not config:
            return None

        # Unset all other defaults of this type and applies_to
        query = select(GenerationConfig).where(
            and_(
                GenerationConfig.config_type == config_type,
                GenerationConfig.applies_to == config.applies_to,
                GenerationConfig.is_default == True,
                GenerationConfig.id != config_id,
            )
        )
        result = await self.db.execute(query)
        existing_defaults = result.scalars().all()

        for existing in existing_defaults:
            existing.is_default = False

        # Set this as default
        config.is_default = True
        await self.db.flush()
        await self.db.refresh(config)

        return config
