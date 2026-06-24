"""Coloring Book Template Pydantic Schemas"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ColoringBookTemplateBase(BaseModel):
    """Base coloring book template schema"""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    long_description: str | None = None
    theme: str = Field(..., min_length=1, max_length=50)
    age_group: Literal["0-2", "3-5", "6-8", "9-12"]
    price: float = Field(..., ge=0, le=999.99)
    cover_image_url: str = Field(..., min_length=1, max_length=500)
    preview_images: list[str] = Field(default_factory=list)
    sample_pages: list[str] = Field(default_factory=list)
    total_pages: int = Field(..., ge=1, le=100)
    page_types: list[str] = Field(default_factory=list)
    customization_options: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        """Validate price has max 2 decimal places"""
        if round(v, 2) != v:
            raise ValueError("Price must have at most 2 decimal places")
        return v


class ColoringBookTemplateCreate(ColoringBookTemplateBase):
    """Schema for creating a coloring book template"""

    is_published: bool = True


class ColoringBookTemplateUpdate(BaseModel):
    """Schema for updating a coloring book template"""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, min_length=1)
    long_description: str | None = None
    theme: str | None = Field(None, min_length=1, max_length=50)
    age_group: Literal["0-2", "3-5", "6-8", "9-12"] | None = None
    price: float | None = Field(None, ge=0, le=999.99)
    cover_image_url: str | None = Field(None, min_length=1, max_length=500)
    preview_images: list[str] | None = None
    sample_pages: list[str] | None = None
    total_pages: int | None = Field(None, ge=1, le=100)
    page_types: list[str] | None = None
    customization_options: dict[str, Any] | None = None
    tags: list[str] | None = None
    is_published: bool | None = None


class ColoringBookTemplateResponse(ColoringBookTemplateBase):
    """Schema for coloring book template response"""

    id: UUID
    is_published: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ColoringBookTemplateListItem(BaseModel):
    """Simplified schema for coloring book template listing"""

    id: UUID
    title: str
    description: str
    theme: str
    age_group: Literal["0-2", "3-5", "6-8", "9-12"]
    price: float
    cover_image_url: str
    total_pages: int
    tags: list[str]

    model_config = {"from_attributes": True}


class ColoringBookTemplateFilters(BaseModel):
    """Query parameters for filtering coloring book templates"""

    theme: str | None = None
    age_group: Literal["0-2", "3-5", "6-8", "9-12"] | None = None
    min_price: float | None = Field(None, ge=0)
    max_price: float | None = Field(None, ge=0)
    tags: list[str] | None = None
    search: str | None = Field(None, max_length=100)
    sort_by: Literal["title", "price", "created_at"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"
