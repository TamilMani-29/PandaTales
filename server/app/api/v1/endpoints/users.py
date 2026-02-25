"""User Profile API Routes"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import get_logger, success_response
from app.db.session import get_db
from app.schemas.user import (
    AccountDeletionRequest,
    AvatarUploadResponse,
    UserProfileResponse,
    UserUpdate,
)
from app.services.user import UserService

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["User Management"])


# TODO: Add authentication dependency
# For now, we'll use a hardcoded user_id for demonstration
# In production, this should be: Depends(get_current_user)
def get_current_user_id() -> UUID:
    """Temporary function to get current user ID - replace with actual auth"""
    # This should be replaced with actual authentication
    return UUID("00000000-0000-0000-0000-000000000001")


@router.get(
    "/profile",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get user profile",
    description="Get authenticated user's profile information",
)
async def get_user_profile(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get user profile"""
    service = UserService(db)
    user = await service.get_user_profile(user_id)

    response_data = UserProfileResponse.model_validate(user)

    return success_response(
        data=response_data.model_dump(),
        message="Profile retrieved successfully",
    )


@router.patch(
    "/profile",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Update user profile",
    description="Update authenticated user's profile information",
)
async def update_user_profile(
    profile_data: UserUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update user profile"""
    service = UserService(db)
    user = await service.update_user_profile(user_id, profile_data)

    response_data = UserProfileResponse.model_validate(user)

    return success_response(
        data=response_data.model_dump(),
        message="Profile updated successfully",
    )


@router.post(
    "/profile/avatar",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Upload avatar",
    description="Upload or update user avatar image",
)
async def upload_avatar(
    # TODO: Add file upload parameter
    # file: UploadFile = File(...),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Upload user avatar"""
    # TODO: Implement file upload to storage (MinIO/S3)
    # For now, return a placeholder
    avatar_url = "https://cdn.storybloom.com/avatars/placeholder.jpg"

    service = UserService(db)
    await service.update_avatar(user_id, avatar_url)

    response_data = AvatarUploadResponse(avatar_url=avatar_url)

    return success_response(
        data=response_data.model_dump(),
        message="Avatar uploaded successfully",
    )


@router.delete(
    "/account",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Delete account",
    description="Delete user account (requires password confirmation)",
)
async def delete_account(
    deletion_request: AccountDeletionRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Delete user account"""
    service = UserService(db)
    await service.delete_account(
        user_id,
        deletion_request.password,
        deletion_request.confirmation,
    )

    return success_response(
        message="Account deletion initiated. You will receive a confirmation email.",
    )
