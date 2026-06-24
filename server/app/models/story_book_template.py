"""Story Book Template Model"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import BaseModel, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.generated_book import GeneratedBook


class StoryBookTemplate(Base, BaseModel, SoftDeleteMixin):
    """
    Story book template model for personalized story books
    """

    __tablename__ = "story_book_templates"

    # Basic Information
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Type and Categorization
    book_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    series_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    book_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Classification
    genre: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    age_group: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    
    # Story-specific attributes
    story_theme: Mapped[str | None] = mapped_column(String(100), nullable=True)
    moral_lesson: Mapped[str | None] = mapped_column(Text, nullable=True)
    reading_level: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Pricing
    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        index=True,
    )

    # Media
    cover_image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    preview_images: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )

    # Content
    total_pages: Mapped[int] = mapped_column(Integer, nullable=False)
    features: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    learning_outcomes: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    
    # Story structure
    chapters: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )

    # AI generation prompts config — stores story_lines, scenes, backgrounds, negative_prompt etc.
    prompts_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Customization
    customization_options: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    # Metadata
    tags: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )

    # Status
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    # Relationships
    # generated_books: Mapped[list["GeneratedBook"]] = relationship(
    #     "GeneratedBook",
    #     back_populates="story_template",
    #     lazy="selectin",
    # )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "book_type IN ('single', 'series') OR book_type IS NULL",
            name="check_story_book_type",
        ),
        CheckConstraint(
            "age_group IN ('0-2', '3-5', '6-8', '9-12')",
            name="check_story_age_group",
        ),
        CheckConstraint(
            "reading_level IN ('beginner', 'intermediate', 'advanced') OR reading_level IS NULL",
            name="check_reading_level",
        ),
        CheckConstraint("price >= 0", name="check_story_price_positive"),
        CheckConstraint("total_pages > 0", name="check_story_total_pages_positive"),
        Index("idx_story_templates_active_published", "is_active", "is_published"),
        Index("idx_story_templates_genre", "genre"),
        Index("idx_story_templates_series", "series_id", "book_number"),
        Index(
            "idx_story_templates_search",
            text("to_tsvector('english', title || ' ' || description)"),
            postgresql_using="gin",
        ),
        Index("idx_story_templates_tags", "tags", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<StoryBookTemplate(id={self.id}, title='{self.title}')>"
