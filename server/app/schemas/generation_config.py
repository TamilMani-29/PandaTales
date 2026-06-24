"""Generation Configuration Schemas - Admin Settings"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Base Schema
class GenerationConfigBase(BaseModel):
    """Base schema for generation configurations"""

    config_type: Literal["theme", "prompt_template", "style_preset", "generation_parameter"]
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    icon_url: str | None = None
    preview_image_url: str | None = None
    config_data: dict[str, Any] = Field(..., description="JSON configuration data")
    category: str | None = Field(None, max_length=50)
    tags: list[str] | None = None
    applies_to: Literal["story_book", "coloring_book", "both"] = "coloring_book"
    max_photos: int = Field(default=20, ge=1, le=50)
    min_photos: int = Field(default=1, ge=1, le=50)
    is_active: bool = True
    is_premium: bool = False
    is_default: bool = False
    sort_order: int = 0


# Create Schema
class GenerationConfigCreate(GenerationConfigBase):
    """Schema for creating a generation configuration"""

    pass


# Update Schema
class GenerationConfigUpdate(BaseModel):
    """Schema for updating a generation configuration"""

    display_name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    icon_url: str | None = None
    preview_image_url: str | None = None
    config_data: dict[str, Any] | None = None
    category: str | None = None
    tags: list[str] | None = None
    applies_to: Literal["story_book", "coloring_book", "both"] | None = None
    max_photos: int | None = Field(None, ge=1, le=50)
    min_photos: int | None = Field(None, ge=1, le=50)
    is_active: bool | None = None
    is_premium: bool | None = None
    is_default: bool | None = None
    sort_order: int | None = None


# Response Schema
class GenerationConfigResponse(GenerationConfigBase):
    """Schema for generation configuration response"""

    id: UUID
    usage_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# List Item Schema
class GenerationConfigListItem(BaseModel):
    """Schema for configuration list items"""

    id: UUID
    config_type: Literal["theme", "prompt_template", "style_preset", "generation_parameter"]
    name: str
    display_name: str
    description: str | None = None
    icon_url: str | None = None
    preview_image_url: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    applies_to: Literal["story_book", "coloring_book", "both"]
    is_active: bool
    is_premium: bool
    is_default: bool
    usage_count: int
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


# Filters
class GenerationConfigFilters(BaseModel):
    """Filters for listing generation configurations"""

    config_type: Literal["theme", "prompt_template", "style_preset", "generation_parameter"] | None = None
    category: str | None = None
    applies_to: Literal["story_book", "coloring_book", "both"] | None = None
    is_active: bool | None = None
    is_premium: bool | None = None
    search: str | None = Field(None, max_length=100)
    sort: Literal["name", "usage", "recent", "sort_order"] = "sort_order"


# Theme-specific schemas for easier theme management
class ThemeConfigData(BaseModel):
    """Structure for theme configuration data"""

    base_prompt: str = Field(..., description="Base prompt template for theme")
    style_parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Style parameters like line_weight, detail_level, etc.",
    )
    sample_keywords: list[str] = Field(
        default_factory=list,
        description="Keywords that represent this theme",
    )
    generation_settings: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional AI generation settings",
    )


class ThemeCreate(BaseModel):
    """Simplified schema for creating themes"""

    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    icon_url: str | None = None
    preview_image_url: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    max_photos: int = Field(default=20, ge=1, le=50)
    min_photos: int = Field(default=1, ge=1, le=50)
    is_premium: bool = False
    
    # Theme-specific data
    base_prompt: str = Field(..., description="Base prompt for generation")
    style_parameters: dict[str, Any] = Field(default_factory=dict)
    sample_keywords: list[str] = Field(default_factory=list)
    generation_settings: dict[str, Any] = Field(default_factory=dict)


class ThemeUpdate(BaseModel):
    """Simplified schema for updating themes"""

    display_name: str | None = None
    description: str | None = None
    icon_url: str | None = None
    preview_image_url: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    max_photos: int | None = Field(None, ge=1, le=50)
    min_photos: int | None = Field(None, ge=1, le=50)
    is_active: bool | None = None
    is_premium: bool | None = None
    is_default: bool | None = None
    sort_order: int | None = None
    
    # Theme-specific data
    base_prompt: str | None = None
    style_parameters: dict[str, Any] | None = None
    sample_keywords: list[str] | None = None
    generation_settings: dict[str, Any] | None = None


# Public theme list (for users selecting themes)
class PublicThemeItem(BaseModel):
    """Public theme information for user selection"""

    id: UUID
    name: str
    display_name: str
    description: str | None = None
    icon_url: str | None = None
    preview_image_url: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    is_premium: bool
    is_default: bool
    min_photos: int
    max_photos: int

    model_config = ConfigDict(from_attributes=True)
