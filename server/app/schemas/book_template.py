"""Book Template Pydantic Schemas"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class BookTemplateBase(BaseModel):
    """Base book template schema"""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    long_description: str | None = None
    template_type: Literal["story_book", "coloring_book"]
    book_type: Literal["single", "series"] | None = None
    series_id: UUID | None = None
    book_number: int | None = Field(None, ge=1)
    genre: str = Field(..., min_length=1, max_length=50)
    age_group: Literal["0-2", "3-5", "6-8", "9-12"]
    difficulty: Literal["easy", "medium", "hard"] | None = None
    price: float = Field(..., ge=0, le=999.99)
    cover_image_url: str = Field(..., min_length=1, max_length=500)
    preview_images: list[str] = Field(default_factory=list)
    total_pages: int = Field(..., ge=1, le=100)
    features: list[str] = Field(default_factory=list)
    learning_outcomes: list[str] = Field(default_factory=list)
    customization_options: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        """Validate price has max 2 decimal places"""
        if round(v, 2) != v:
            raise ValueError("Price must have at most 2 decimal places")
        return v


class BookTemplateCreate(BookTemplateBase):
    """Schema for creating a book template"""

    is_published: bool = True


class BookTemplateUpdate(BaseModel):
    """Schema for updating a book template"""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, min_length=1)
    long_description: str | None = None
    book_type: Literal["single", "series"] | None = None
    series_id: UUID | None = None
    book_number: int | None = Field(None, ge=1)
    genre: str | None = Field(None, min_length=1, max_length=50)
    age_group: Literal["0-2", "3-5", "6-8", "9-12"] | None = None
    difficulty: Literal["easy", "medium", "hard"] | None = None
    price: float | None = Field(None, ge=0, le=999.99)
    cover_image_url: str | None = Field(None, min_length=1, max_length=500)
    preview_images: list[str] | None = None
    total_pages: int | None = Field(None, ge=1, le=100)
    features: list[str] | None = None
    learning_outcomes: list[str] | None = None
    customization_options: dict[str, Any] | None = None
    tags: list[str] | None = None
    is_published: bool | None = None


class BookTemplateResponse(BookTemplateBase):
    """Schema for book template response"""

    id: UUID
    is_published: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookTemplateListItem(BaseModel):
    """Simplified schema for template listing"""

    id: UUID
    title: str
    description: str
    template_type: Literal["story_book", "coloring_book"]
    genre: str
    age_group: Literal["0-2", "3-5", "6-8", "9-12"]
    difficulty: Literal["easy", "medium", "hard"] | None
    price: float
    cover_image_url: str
    total_pages: int
    tags: list[str]

    model_config = {"from_attributes": True}


class BookTemplateFilters(BaseModel):
    """Query parameters for filtering templates"""

    template_type: Literal["story_book", "coloring_book"] | None = None
    genre: str | None = None
    age_group: Literal["0-2", "3-5", "6-8", "9-12"] | None = None
    difficulty: Literal["easy", "medium", "hard"] | None = None
    min_price: float | None = Field(None, ge=0)
    max_price: float | None = Field(None, ge=0)
    tags: list[str] | None = None
    search: str | None = Field(None, max_length=100)
    sort_by: Literal["title", "price", "created_at"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"


class BookTemplateSeriesInfo(BaseModel):
    """Information about series templates"""

    series_id: UUID
    series_title: str
    book_count: int
    books: list[BookTemplateListItem]
