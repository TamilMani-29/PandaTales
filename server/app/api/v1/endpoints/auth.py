"""Authentication API routes."""

from typing import Any

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    DirectResetPasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Register user",
    description="Create a user account and return JWT access token.",
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = AuthService(db)
    data = await service.register(payload)
    return success_response(data=data.model_dump(), message="Account created successfully")


@router.post(
    "/login",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Login user",
    description="Authenticate user and return JWT access token.",
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = AuthService(db)
    data = await service.login(payload)
    return success_response(data=data.model_dump(), message="Login successful")


@router.post(
    "/forgot-password",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Send a password reset link if the account exists.",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = AuthService(db)
    await service.request_password_reset(
        email=payload.email,
        redirect_base_url=payload.redirect_base_url,
        requested_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return success_response(
        data={"sent": True},
        message="If an account exists for this email, a reset link has been sent",
    )


@router.post(
    "/reset-password",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Reset password",
    description="Set a new password using a valid forgot-password token.",
)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = AuthService(db)
    await service.reset_password(token=payload.token, new_password=payload.new_password)
    return success_response(data={"updated": True}, message="Password has been reset successfully")


@router.post(
    "/forgot-password/direct-reset",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Direct forgot-password reset",
    description="Reset password directly from the in-app forgot-password flow.",
)
async def direct_reset_password(
    payload: DirectResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = AuthService(db)
    await service.direct_reset_password(email=payload.email, new_password=payload.new_password)
    return success_response(data={"updated": True}, message="Password has been reset successfully")


@router.get(
    "/me",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Return authenticated user profile from JWT.",
)
async def me(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    full_name = current_user.full_name or f"{current_user.first_name} {current_user.last_name}".strip()
    return success_response(
        data={
            "id": str(current_user.id),
            "email": current_user.email,
            "full_name": full_name,
            "phone": current_user.phone,
            "referral_code": current_user.referral_code,
            "referral_count": current_user.referral_count,
        },
        message="User profile retrieved",
    )
