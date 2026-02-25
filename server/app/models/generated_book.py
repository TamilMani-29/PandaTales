"""Generated Book Model (placeholder for relationships)"""

from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import BaseModel


class GeneratedBook(Base, BaseModel):
    """Generated book model - minimal for now"""

    __tablename__ = "generated_books"

    template_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("book_templates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    child_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationship
    template: Mapped["BookTemplate"] = relationship(
        "BookTemplate",
        back_populates="generated_books",
    )
