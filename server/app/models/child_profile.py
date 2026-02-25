"""Child Profile Model"""

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import BaseModel, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.user import User


class ChildProfile(Base, BaseModel, SoftDeleteMixin):
    """
    Child profile model for personalized book generation
    """

    __tablename__ = "child_profiles"

    # Foreign Key
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic Information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Media
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Statistics
    books_created_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="children",
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "age >= 0 AND age <= 18",
            name="check_child_age_range",
        ),
        CheckConstraint(
            "gender IN ('male', 'female', 'other')",
            name="check_child_gender",
        ),
        Index("idx_child_profiles_user_active", "user_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<ChildProfile(id={self.id}, name={self.name}, age={self.age})>"
