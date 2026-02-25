"""Pydantic schemas"""

from app.schemas.book_template import (
    BookTemplateCreate,
    BookTemplateFilters,
    BookTemplateListItem,
    BookTemplateResponse,
    BookTemplateSeriesInfo,
    BookTemplateUpdate,
)
from app.schemas.user import (
    AccountDeletionRequest,
    AddressCreate,
    AddressListResponse,
    AddressResponse,
    AddressUpdate,
    AvatarUploadResponse,
    ChildProfileCreate,
    ChildProfileListResponse,
    ChildProfileResponse,
    ChildProfileUpdate,
    UserCreate,
    UserProfileResponse,
    UserUpdate,
)

__all__ = [
    "BookTemplateCreate",
    "BookTemplateUpdate",
    "BookTemplateResponse",
    "BookTemplateListItem",
    "BookTemplateFilters",
    "BookTemplateSeriesInfo",
    # User schemas
    "AccountDeletionRequest",
    "AddressCreate",
    "AddressListResponse",
    "AddressResponse",
    "AddressUpdate",
    "AvatarUploadResponse",
    "ChildProfileCreate",
    "ChildProfileListResponse",
    "ChildProfileResponse",
    "ChildProfileUpdate",
    "UserCreate",
    "UserProfileResponse",
    "UserUpdate",
]
