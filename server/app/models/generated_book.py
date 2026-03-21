"""Generated Book Model"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.child_profile import ChildProfile
    from app.models.generation_config import GenerationConfig
    from app.models.user import User
    from app.models.order import Order


class GeneratedBook(Base, BaseModel):
    """Generated book model - supports both story and coloring books"""

    __tablename__ = "generated_books"

    # User relationship
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Polymorphic template reference
    template_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    template_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Generation type (for coloring books)
    generation_type: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True,
    )  # 'photo_to_coloring', 'theme_based', null for story books

    # Theme configuration (for theme-based generation)
    theme_config_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("generation_configs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    selected_theme_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Denormalized for quick access

    # Child information (can reference child_profiles or be standalone)
    child_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("child_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    child_name: Mapped[str] = mapped_column(String(100), nullable=False)
    child_age: Mapped[int] = mapped_column(Integer, nullable=False)
    child_gender: Mapped[str] = mapped_column(String(20), nullable=False)

    # Generation status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="queued",
        index=True,
    )
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Queue information
    queue_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_completion_time: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # seconds

    # Generation steps tracking
    generation_steps: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Photos uploaded for generation
    photos: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=[]
    )

    # Generated content
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preview_pages: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    # Purchase status
    is_purchased: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    purchased_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timing
    generation_duration: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # seconds
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Error tracking
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Notification / delivery contact
    parent_email: Mapped[str] = mapped_column(String(255), nullable=False)
    whatsapp_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="generated_books")
    child: Mapped["ChildProfile | None"] = relationship(
        "ChildProfile", back_populates="generated_books"
    )
    theme_config: Mapped["GenerationConfig | None"] = relationship(
        "GenerationConfig"
    )
    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="book",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "template_type IN ('story_book', 'coloring_book')",
            name="check_template_type",
        ),
        CheckConstraint(
            "generation_type IN ('photo_to_coloring', 'theme_based') OR generation_type IS NULL",
            name="check_generation_type",
        ),
        CheckConstraint(
            "status IN ('queued', 'processing', 'completed', 'failed', 'cancelled')",
            name="check_status",
        ),
        CheckConstraint(
            "progress >= 0 AND progress <= 100",
            name="check_progress_range",
        ),
        CheckConstraint(
            "child_age > 0 AND child_age <= 18",
            name="check_child_age",
        ),
        Index("idx_generated_books_user_status", "user_id", "status"),
        Index("idx_generated_books_status_created", "status", "created_at"),
        Index("idx_generated_books_generation_type", "generation_type"),
    )

    def __repr__(self) -> str:
        return f"<GeneratedBook(id={self.id}, template_type='{self.template_type}', child_name='{self.child_name}', status='{self.status}')>"
