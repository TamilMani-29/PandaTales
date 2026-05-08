"""Schemas for authentication endpoints."""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """User registration payload."""

    full_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    referral_code: str | None = Field(None, min_length=3, max_length=20)


class LoginRequest(BaseModel):
    """User login payload."""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=100)


class AuthUserResponse(BaseModel):
    """User shape returned after auth/me calls."""

    id: str
    email: EmailStr
    full_name: str
    referral_code: str
    referral_count: int


class AuthResponse(BaseModel):
    """Authentication success payload."""

    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse
