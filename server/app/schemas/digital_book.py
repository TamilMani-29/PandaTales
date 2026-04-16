"""Pydantic schemas for digital book catalog APIs."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.core.constants import AgeGroup, BookType, Language, Style, Theme


class DigitalBookCreateRequest(BaseModel):
    """Payload for creating a digital book catalog entry."""

    book_name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    total_pages: int | None = Field(None, ge=1)
    book_type: BookType
    theme: Theme
    style: Style
    age_group: AgeGroup
    language: Language = Language.ENGLISH
    genre: str = Field(..., min_length=1, max_length=100)
    price: Decimal | None = Field(None, ge=0)


class DigitalBookResponse(BaseModel):
    """Response model for digital book item."""

    id: int
    book_name: str
    description: str | None
    cover_image_url: str | None
    cover_image_presigned_url: str | None
    book_url: str | None
    total_pages: int | None
    book_type: BookType | None
    theme: Theme | None
    style: Style | None
    age_group: AgeGroup | None
    language: Language | None
    genre_id: int | None
    genre_name: str | None
    price: float | None
    rating: float
    total_ratings: int
    download_count: int
    created_at: datetime
    updated_at: datetime


class DigitalBookListResponse(BaseModel):
    """Response model for listing digital books."""

    books: list[DigitalBookResponse]


class SendPdfEmailRequest(BaseModel):
    """Request model to email a book PDF to a user."""

    book_id: int = Field(..., ge=1)
    email: EmailStr
