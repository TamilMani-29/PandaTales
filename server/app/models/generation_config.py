"""Generation Configuration Model - Admin configurable settings"""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import BaseModel


class GenerationConfig(Base, BaseModel):
    """
    Admin-configurable generation settings for themes, prompts, and parameters
    """

    __tablename__ = "generation_configs"

    # Configuration identification
    config_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # 'theme', 'prompt_template', 'style_preset', etc.

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # Display information
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    preview_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Configuration data (JSON structure)
    config_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # Example for theme:
    # {
    #   "base_prompt": "Create coloring pages with {theme_description}",
    #   "style_parameters": {"line_weight": "medium", "detail_level": "high"},
    #   "sample_keywords": ["animals", "nature", "outdoor"]
    # }
    # Example for prompt_template:
    # {
    #   "template": "Generate a coloring page of {subject} in {style} style",
    #   "required_vars": ["subject", "style"],
    #   "defaults": {"style": "cartoon"}
    # }

    # Categorization
    category: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    tags: Mapped[list[str] | None] = mapped_column(
        JSONB, nullable=True
    )  # For filtering and search

    # Applicability
    applies_to: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="coloring_book",
    )  # 'story_book', 'coloring_book', 'both'

    # Generation parameters
    max_photos: Mapped[int] = mapped_column(
        Integer, nullable=False, default=20
    )  # Max photos for this config
    min_photos: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )  # Min photos required

    # Visibility and status
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    is_premium: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # Premium feature flag
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # Default selection

    # Ordering
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # For display ordering

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # Track popularity

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "config_type IN ('theme', 'prompt_template', 'style_preset', 'generation_parameter')",
            name="check_config_type",
        ),
        CheckConstraint(
            "applies_to IN ('story_book', 'coloring_book', 'both')",
            name="check_applies_to",
        ),
        CheckConstraint(
            "max_photos >= min_photos",
            name="check_photo_range",
        ),
        CheckConstraint(
            "max_photos <= 50",
            name="check_max_photos_limit",
        ),
        Index("idx_configs_type_active", "config_type", "is_active"),
        Index("idx_configs_category", "category"),
    )

    def __repr__(self) -> str:
        return f"<GenerationConfig(id={self.id}, type='{self.config_type}', name='{self.name}')>"
