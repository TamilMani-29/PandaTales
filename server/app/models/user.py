"""User Model"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime

from app.db.session import Base
from app.models.base import BaseModel, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.child_profile import ChildProfile
    from app.models.address import Address
    from app.models.generated_book import GeneratedBook
    from app.models.order import Order


class User(Base, BaseModel, SoftDeleteMixin):
    """
    User account model for authentication and profile management
    """

    __tablename__ = "users"

    # Authentication
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,  # Nullable for OAuth users
    )

    # Profile Information
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    referral_code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    referral_count: Mapped[int] = mapped_column(default=0, nullable=False)

    # Verification Status
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # OAuth Integration
    oauth_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    oauth_provider_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Role and Access
    role: Mapped[str] = mapped_column(
        String(20),
        default="user",
        nullable=False,
    )

    # Activity Tracking
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    children: Mapped[list["ChildProfile"]] = relationship(
        "ChildProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    addresses: Mapped[list["Address"]] = relationship(
        "Address",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    generated_books: Mapped[list["GeneratedBook"]] = relationship(
        "GeneratedBook",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'admin')",
            name="check_user_role",
        ),
        CheckConstraint(
            "oauth_provider IN ('google', 'facebook', 'apple')",
            name="check_oauth_provider",
        ),
        Index("idx_users_oauth", "oauth_provider", "oauth_provider_id"),
        Index("idx_users_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
