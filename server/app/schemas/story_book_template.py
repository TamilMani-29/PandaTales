"""Story Book Template Pydantic Schemas"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class StoryBookTemplateBase(BaseModel):
    """Base story book template schema"""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    long_description: str | None = None
    book_type: Literal["single", "series"] | None = None
    series_id: UUID | None = None
    book_number: int | None = Field(None, ge=1)
    genre: str = Field(..., min_length=1, max_length=50)
    age_group: Literal["0-2", "3-5", "6-8", "9-12"]
    story_theme: str | None = Field(None, max_length=100)
    moral_lesson: str | None = None
    reading_level: Literal["beginner", "intermediate", "advanced"] | None = None
    price: float = Field(..., ge=0, le=999.99)
    cover_image_url: str = Field(..., min_length=1, max_length=500)
    preview_images: list[str] = Field(default_factory=list)
    total_pages: int = Field(..., ge=1, le=100)
    features: list[str] = Field(default_factory=list)
    learning_outcomes: list[str] = Field(default_factory=list)
    chapters: list[dict[str, Any]] = Field(default_factory=list)
    customization_options: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        """Validate price has max 2 decimal places"""
        if round(v, 2) != v:
            raise ValueError("Price must have at most 2 decimal places")
        return v


class StoryBookTemplateCreate(StoryBookTemplateBase):
    """Schema for creating a story book template"""

    is_published: bool = True


class StoryBookTemplateUpdate(BaseModel):
    """Schema for updating a story book template"""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, min_length=1)
    long_description: str | None = None
    book_type: Literal["single", "series"] | None = None
    series_id: UUID | None = None
    book_number: int | None = Field(None, ge=1)
    genre: str | None = Field(None, min_length=1, max_length=50)
    age_group: Literal["0-2", "3-5", "6-8", "9-12"] | None = None
    story_theme: str | None = Field(None, max_length=100)
    moral_lesson: str | None = None
    reading_level: Literal["beginner", "intermediate", "advanced"] | None = None
    price: float | None = Field(None, ge=0, le=999.99)
    cover_image_url: str | None = Field(None, min_length=1, max_length=500)
    preview_images: list[str] | None = None
    total_pages: int | None = Field(None, ge=1, le=100)
    features: list[str] | None = None
    learning_outcomes: list[str] | None = None
    chapters: list[dict[str, Any]] | None = None
    customization_options: dict[str, Any] | None = None
    tags: list[str] | None = None
    is_published: bool | None = None


class StoryBookTemplateResponse(StoryBookTemplateBase):
    """Schema for story book template response"""

    id: UUID
    is_published: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StoryBookTemplateListItem(BaseModel):
    """Simplified schema for story book template listing"""

    id: UUID
    title: str
    description: str
    genre: str
    age_group: Literal["0-2", "3-5", "6-8", "9-12"]
    reading_level: Literal["beginner", "intermediate", "advanced"] | None
    price: float
    cover_image_url: str
    total_pages: int
    tags: list[str]

    model_config = {"from_attributes": True}


class StoryBookTemplateFilters(BaseModel):
    """Query parameters for filtering story book templates"""

    genre: str | None = None
    age_group: Literal["0-2", "3-5", "6-8", "9-12"] | None = None
    reading_level: Literal["beginner", "intermediate", "advanced"] | None = None
    min_price: float | None = Field(None, ge=0)
    max_price: float | None = Field(None, ge=0)
    tags: list[str] | None = None
    search: str | None = Field(None, max_length=100)
    sort_by: Literal["title", "price", "created_at"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"


class StoryBookTemplateSeriesInfo(BaseModel):
    """Information about story book series templates"""

    series_id: UUID
    series_title: str
    book_count: int
    books: list[StoryBookTemplateListItem]
