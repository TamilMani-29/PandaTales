"""Catalog books model with fixed enum-driven attributes."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import AgeGroup, BookType, Language, Style, Theme
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.genre import Genre


class Book(Base):
    """Book catalog entity for story and coloring products."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    book_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)

    book_type: Mapped[BookType | None] = mapped_column(
        Enum(
            BookType,
            name="book_type_enum",
            native_enum=True,
            validate_strings=True,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=True,
    )
    theme: Mapped[Theme | None] = mapped_column(
        Enum(
            Theme,
            name="theme_enum",
            native_enum=True,
            validate_strings=True,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=True,
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
    language: Mapped[Language | None] = mapped_column(
        Enum(
            Language,
            name="language_enum",
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
        return f"<Book(id={self.id}, name='{self.book_name}', type={self.book_type})>"
