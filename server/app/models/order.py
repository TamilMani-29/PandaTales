"""Order Model - Razorpay payment orders"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.generated_book import GeneratedBook


class Order(Base, BaseModel):
    """
    Payment order — one record per checkout attempt.
    A 'razorpay_order_id' is created first; after the user pays, the
    razorpay_payment_id and razorpay_signature are stored and verified.
    """

    __tablename__ = "orders"

    # Owning user
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Which book is being purchased
    book_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("generated_books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # What the user is buying: 'digital' | 'softcover' | 'hardcover'
    format: Mapped[str] = mapped_column(String(20), nullable=False)

    # Amount in paise (INR smallest unit). e.g. ₹499 → 49900
    amount: Mapped[int] = mapped_column(Integer, nullable=False)

    # Currency — always INR for now
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")

    # Razorpay identifiers
    razorpay_order_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    razorpay_payment_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    razorpay_signature: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # Order lifecycle: 'created' → 'paid' | 'failed'
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="created", index=True
    )

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Delivery contact
    whatsapp_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    book: Mapped["GeneratedBook"] = relationship("GeneratedBook", back_populates="orders")
