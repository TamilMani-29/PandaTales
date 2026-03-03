"""Coloring Book Template Model"""

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


class ColoringBookTemplate(Base, BaseModel, SoftDeleteMixin):
    """
    Coloring book template model for coloring activity books
    """

    __tablename__ = "coloring_book_templates"

    # Basic Information
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Classification
    theme: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    age_group: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

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
    sample_pages: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )

    # Content
    total_pages: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Coloring page types
    page_types: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )

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
    #     back_populates="coloring_template",
    #     lazy="selectin",
    # )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "age_group IN ('0-2', '3-5', '6-8', '9-12')",
            name="check_coloring_age_group",
        ),
        CheckConstraint("price >= 0", name="check_coloring_price_positive"),
        CheckConstraint("total_pages > 0", name="check_coloring_total_pages_positive"),
        Index("idx_coloring_templates_active_published", "is_active", "is_published"),
        Index("idx_coloring_templates_theme", "theme"),
        Index(
            "idx_coloring_templates_search",
            text("to_tsvector('english', title || ' ' || description)"),
            postgresql_using="gin",
        ),
        Index("idx_coloring_templates_tags", "tags", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<ColoringBookTemplate(id={self.id}, title='{self.title}', theme='{self.theme}')>"
