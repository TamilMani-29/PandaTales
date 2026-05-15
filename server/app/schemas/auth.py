"""Schemas for authentication endpoints."""

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """User registration payload."""

    full_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    referral_code: str | None = Field(None, min_length=3, max_length=20)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = "".join(ch for ch in value.strip() if ch.isdigit())
        if len(normalized) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        return normalized[-15:]


class LoginRequest(BaseModel):
    """User login payload."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Password is required")
        return value


class AuthUserResponse(BaseModel):
    """User shape returned after auth/me calls."""

    id: str
    email: EmailStr
    full_name: str
    phone: str | None = None
    referral_code: str
    referral_count: int


class AuthResponse(BaseModel):
    """Authentication success payload."""

    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse
