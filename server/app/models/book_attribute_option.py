"""Configurable attribute options for digital book catalog."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class BookAttributeOption(Base):
    """Persist admin-managed dropdown options for book metadata fields."""

    __tablename__ = "book_attribute_options"
    __table_args__ = (
        UniqueConstraint("option_type", "value", name="uq_book_attribute_options_type_value"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    option_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    value: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
