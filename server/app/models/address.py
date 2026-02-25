"""Address Model"""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import BaseModel, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.user import User


class Address(Base, BaseModel, SoftDeleteMixin):
    """
    Address model for shipping and billing
    """

    __tablename__ = "addresses"

    # Foreign Key
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Name Information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Address Information
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
    )  # ISO 3166-1 alpha-2

    # Contact
    phone: Mapped[str] = mapped_column(String(20), nullable=False)

    # Flags
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="addresses",
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "length(country) = 2",
            name="check_country_code_length",
        ),
        Index("idx_addresses_user_default", "user_id", "is_default"),
        # Ensure only one default address per user
        Index(
            "idx_addresses_user_default_unique",
            "user_id",
            unique=True,
            postgresql_where="(is_default = TRUE AND is_active = TRUE)",
        ),
    )

    def __repr__(self) -> str:
        return f"<Address(id={self.id}, city={self.city}, country={self.country})>"
