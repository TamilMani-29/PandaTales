"""Catalog books model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import AgeGroup, Style
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.book_attribute_option import BookAttributeOption
    from app.models.genre import Genre


class Book(Base):
    """Book catalog entity for story and coloring products."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    emoji: Mapped[str | None] = mapped_column(String(16), nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    front_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    back_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_1_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_2_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_3_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_4_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    book_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    age_label: Mapped[str | None] = mapped_column(String(32), nullable=True)
    style_label: Mapped[str | None] = mapped_column(String(64), nullable=True)

    book_type_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("book_attribute_options.id"), nullable=True
    )
    theme_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("book_attribute_options.id"), nullable=True
    )
    language_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("book_attribute_options.id"), nullable=True
    )
    style: Mapped[Style | None] = mapped_column(
        Enum(
            Style,
            name="style_enum",
            native_enum=True,
            validate_strings=True,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=True,
    )
    age_group: Mapped[AgeGroup | None] = mapped_column(
        Enum(
            AgeGroup,
            name="age_group_enum",
            native_enum=True,
            validate_strings=True,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=True,
    )
    genre_id: Mapped[int | None] = mapped_column(
        ForeignKey("genres.id"),
        nullable=True,
        index=True,
    )

    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    total_ratings: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    download_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_bestseller: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_personalized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    genre: Mapped["Genre | None"] = relationship("Genre", back_populates="books")

    def __repr__(self) -> str:
        return f"<Book(id={self.id}, name='{self.book_name}', book_type_id={self.book_type_id})>"
