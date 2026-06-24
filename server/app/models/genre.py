"""Genre catalog model."""

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.book import Book


class Genre(Base):
    """Genre values used by catalog books."""

    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    books: Mapped[list["Book"]] = relationship("Book", back_populates="genre")

    def __repr__(self) -> str:
        return f"<Genre(id={self.id}, name='{self.name}')>"
