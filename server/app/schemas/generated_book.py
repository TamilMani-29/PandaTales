"""Generated Book Schemas"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Base Schema
class GeneratedBookBase(BaseModel):
    """Base schema for generated books"""

    template_type: Literal["story_book", "coloring_book"]
    template_id: UUID
    child_name: str = Field(..., min_length=1, max_length=100)
    child_age: int = Field(..., gt=0, le=18)
    child_gender: Literal["male", "female", "other"]


# Generation Request
class BookGenerationCreate(BaseModel):
    """Schema for initiating book generation"""

    template_id: UUID
    template_type: Literal["story_book", "coloring_book"]
    child_id: UUID | None = None
    child_name: str | None = Field(None, min_length=1, max_length=100)
    child_age: int | None = Field(None, gt=0, le=18)
    child_gender: Literal["male", "female", "other"] | None = None
    parent_email: str | None = Field(None, pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    # photos will be handled separately as file uploads

    @field_validator("child_name", mode="after")
    @classmethod
    def validate_child_name(cls, v: str | None, info) -> str | None:
        """Validate child_name is provided if child_id is not"""
        if not info.data.get("child_id") and not v:
            raise ValueError("child_name is required when child_id is not provided")
        return v

    @field_validator("child_age", mode="after")
    @classmethod
    def validate_child_age(cls, v: int | None, info) -> int | None:
        """Validate child_age is provided if child_id is not"""
        if not info.data.get("child_id") and not v:
            raise ValueError("child_age is required when child_id is not provided")
        return v

    @field_validator("child_gender", mode="after")
    @classmethod
    def validate_child_gender(cls, v: str | None, info) -> str | None:
        """Validate child_gender is provided if child_id is not"""
        if not info.data.get("child_id") and not v:
            raise ValueError("child_gender is required when child_id is not provided")
        return v


# Coloring Book - Photo to Coloring Generation
class PhotoToColoringGenerationCreate(BaseModel):
    """Schema for photo-to-coloring generation (direct conversion)"""

    child_id: UUID | None = None
    child_name: str | None = Field(None, min_length=1, max_length=100)
    child_age: int | None = Field(None, gt=0, le=18)
    child_gender: Literal["male", "female", "other"] | None = None
    parent_email: str | None = Field(None, pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    
    # Processing options
    line_weight: Literal["thin", "medium", "thick"] = "medium"
    detail_level: Literal["low", "medium", "high"] = "medium"
    simplification_level: Literal["minimal", "moderate", "high"] = "moderate"

    @field_validator("child_name", mode="after")
    @classmethod
    def validate_child_name(cls, v: str | None, info) -> str | None:
        if not info.data.get("child_id") and not v:
            raise ValueError("child_name is required when child_id is not provided")
        return v

    @field_validator("child_age", mode="after")
    @classmethod
    def validate_child_age(cls, v: int | None, info) -> int | None:
        if not info.data.get("child_id") and not v:
            raise ValueError("child_age is required when child_id is not provided")
        return v

    @field_validator("child_gender", mode="after")
    @classmethod
    def validate_child_gender(cls, v: str | None, info) -> str | None:
        # child_gender is optional — not all frontends collect it
        return v


# Coloring Book - Theme-Based Generation
class ThemeBasedGenerationCreate(BaseModel):
    """Schema for theme-based coloring book generation"""

    child_id: UUID | None = None
    child_name: str | None = Field(None, min_length=1, max_length=100)
    child_age: int | None = Field(None, gt=0, le=18)
    child_gender: Literal["male", "female", "other"] | None = None
    parent_email: str | None = Field(None, pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    
    # Theme selection
    theme_config_id: UUID  # Reference to admin-configured theme
    
    # Number of pages to generate
    num_pages: int = Field(default=10, ge=5, le=30)
    
    # Style customization
    coloring_style: Literal["simple", "detailed", "mandala", "cartoon"] = "simple"
    
    # photos (1-20) for theme extraction will be handled separately

    @field_validator("child_name", mode="after")
    @classmethod
    def validate_child_name(cls, v: str | None, info) -> str | None:
        if not info.data.get("child_id") and not v:
            raise ValueError("child_name is required when child_id is not provided")
        return v

    @field_validator("child_age", mode="after")
    @classmethod
    def validate_child_age(cls, v: int | None, info) -> int | None:
        if not info.data.get("child_id") and not v:
            raise ValueError("child_age is required when child_id is not provided")
        return v

    @field_validator("child_gender", mode="after")
    @classmethod
    def validate_child_gender(cls, v: str | None, info) -> str | None:
        # child_gender is optional — not all frontends collect it
        return v


# Generation Status Response
class GenerationStepStatus(BaseModel):
    """Status of individual generation steps"""

    photo_processing: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    story_generation: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    image_generation: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    pdf_generation: Literal["pending", "in_progress", "completed", "failed"] = "pending"


class GenerationStatusQueued(BaseModel):
    """Generation status when queued"""

    generation_id: UUID
    status: Literal["queued"]
    queue_position: int
    estimated_wait_time: int  # seconds
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GenerationStatusProcessing(BaseModel):
    """Generation status when processing"""

    generation_id: UUID
    status: Literal["processing"]
    progress: int = Field(..., ge=0, le=100)
    current_step: str
    steps: GenerationStepStatus
    estimated_completion_time: int  # seconds

    model_config = ConfigDict(from_attributes=True)


class GenerationStatusCompleted(BaseModel):
    """Generation status when completed"""

    generation_id: UUID
    status: Literal["completed"]
    book_id: UUID
    progress: int = 100
    completed_at: datetime
    preview_url: str

    model_config = ConfigDict(from_attributes=True)


class GenerationErrorDetail(BaseModel):
    """Error details for failed generation"""

    code: str
    message: str
    details: str | None = None


class GenerationStatusFailed(BaseModel):
    """Generation status when failed"""

    generation_id: UUID
    status: Literal["failed"]
    error: GenerationErrorDetail
    failed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GenerationStatusCancelled(BaseModel):
    """Generation status when cancelled"""

    generation_id: UUID
    status: Literal["cancelled"]
    cancelled_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Initial generation response
class BookGenerationResponse(BaseModel):
    """Response after initiating generation"""

    generation_id: UUID
    status: Literal["queued"]
    estimated_time: int  # seconds
    queue_position: int

    model_config = ConfigDict(from_attributes=True)


# Book Page Schema
class BookPage(BaseModel):
    """Schema for book page preview"""

    page_number: int
    image_url: str
    text: str | None = None


# Template Info (nested)
class TemplateInfo(BaseModel):
    """Template information in book details"""

    title: str
    genre: str | None = None
    theme: str | None = None
    age_group: str


# Child Info (nested)
class ChildInfo(BaseModel):
    """Child information in book details"""

    id: UUID | None = None
    name: str
    age: int
    gender: str


# Generated Book Response
class GeneratedBookResponse(BaseModel):
    """Full generated book details"""

    id: UUID
    template_id: UUID
    template_type: Literal["story_book", "coloring_book"]
    generation_type: Literal["photo_to_coloring", "theme_based"] | None = None
    selected_theme_name: str | None = None
    template: TemplateInfo
    child: ChildInfo
    status: Literal["queued", "processing", "completed", "failed", "cancelled"]
    is_purchased: bool
    cover_image_url: str | None = None
    total_pages: int | None = None
    preview_pages: list[BookPage] | None = None
    generated_at: datetime
    completed_at: datetime | None = None
    generation_duration: int | None = None  # seconds
    progress: int = Field(..., ge=0, le=100)

    model_config = ConfigDict(from_attributes=True)


# List Item Schema
class GeneratedBookListItem(BaseModel):
    """Schema for book list items"""

    id: UUID
    template_id: UUID
    template_type: Literal["story_book", "coloring_book"]
    generation_type: Literal["photo_to_coloring", "theme_based"] | None = None
    selected_theme_name: str | None = None
    template_title: str
    child_name: str
    child_id: UUID | None = None
    status: Literal["queued", "processing", "completed", "failed", "cancelled"]
    cover_image_url: str | None = None
    is_purchased: bool
    purchased_at: datetime | None = None
    generated_at: datetime
    completed_at: datetime | None = None
    preview_url: str | None = None
    download_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


# Filters
class GeneratedBookFilters(BaseModel):
    """Filters for listing generated books"""

    child_id: UUID | None = None
    template_type: Literal["story_book", "coloring_book"] | None = None
    status: Literal["queued", "processing", "completed", "failed", "cancelled"] | None = None
    is_purchased: bool | None = None
    sort: Literal["newest", "oldest", "title"] = "newest"


# Update Schema
class GeneratedBookUpdate(BaseModel):
    """Schema for updating generated book (limited fields)"""

    is_purchased: bool | None = None
    purchased_at: datetime | None = None
