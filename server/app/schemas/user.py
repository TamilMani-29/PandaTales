"""User Schemas"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============ User Profile Schemas ============


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    """Schema for user creation"""

    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for user profile update"""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)

    model_config = ConfigDict(extra="forbid")


class UserProfileResponse(UserBase):
    """Schema for user profile response"""

    id: UUID
    avatar_url: Optional[str] = None
    email_verified: bool
    phone_verified: bool
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AvatarUploadResponse(BaseModel):
    """Response for avatar upload"""

    avatar_url: str


# ============ Child Profile Schemas ============


class ChildProfileBase(BaseModel):
    """Base child profile schema"""

    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=0, le=18)
    gender: str = Field(..., pattern="^(male|female|other)$")
    birth_date: Optional[datetime] = None


class ChildProfileCreate(ChildProfileBase):
    """Schema for child profile creation"""

    pass


class ChildProfileUpdate(BaseModel):
    """Schema for child profile update"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=18)
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    birth_date: Optional[datetime] = None

    model_config = ConfigDict(extra="forbid")


class ChildProfileResponse(ChildProfileBase):
    """Schema for child profile response"""

    id: UUID
    photo_url: Optional[str] = None
    books_created_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChildProfileListResponse(BaseModel):
    """Schema for child profiles list response"""

    children: list[ChildProfileResponse]
    total_count: int


# ============ Address Schemas ============


class AddressBase(BaseModel):
    """Base address schema"""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=2, max_length=2)  # ISO 3166-1 alpha-2
    phone: str = Field(..., min_length=1, max_length=20)
    is_default: bool = False


class AddressCreate(AddressBase):
    """Schema for address creation"""

    pass


class AddressUpdate(BaseModel):
    """Schema for address update"""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    address_line1: Optional[str] = Field(None, min_length=1, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=1, max_length=100)
    postal_code: Optional[str] = Field(None, min_length=1, max_length=20)
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    phone: Optional[str] = Field(None, min_length=1, max_length=20)
    is_default: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")


class AddressResponse(AddressBase):
    """Schema for address response"""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AddressListResponse(BaseModel):
    """Schema for addresses list response"""

    addresses: list[AddressResponse]
    total_count: int


# ============ Account Deletion Schema ============


class AccountDeletionRequest(BaseModel):
    """Schema for account deletion request"""

    password: str = Field(..., min_length=1)
    confirmation: str = Field(..., pattern="^DELETE MY ACCOUNT$")

    model_config = ConfigDict(extra="forbid")
