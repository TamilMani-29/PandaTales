"""User Profile API Routes"""

from typing import Any
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import get_logger, success_response
from app.common.exceptions import BadRequestException, ServiceUnavailableException
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    AccountDeletionRequest,
    AvatarUploadResponse,
    UserProfileResponse,
    UserUpdate,
)
from app.services.user import UserService
from app.services.storage import StorageService

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get(
    "/profile",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get user profile",
    description="Get authenticated user's profile information",
)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get user profile"""
    service = UserService(db)
    user = await service.get_user_profile(current_user.id)

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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update user profile"""
    service = UserService(db)
    user = await service.update_user_profile(current_user.id, profile_data)

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
    description="Upload or update user avatar image (max 5MB, jpg/png/webp)",
)
async def upload_avatar(
    file: UploadFile = File(..., description="Avatar image file"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Upload user avatar to MinIO with proper error handling"""
    
    # Initialize storage service
    storage_service = StorageService()
    
    try:
        # Upload avatar with validation (max 5MB per config)
        object_name = await storage_service.upload_image(
            file=file,
            prefix="avatars",
            max_size_mb=5,
        )
        
        # Generate URL for the uploaded avatar
        # For avatars, use presigned URL (private storage)
        avatar_url = await storage_service.get_file_url(object_name)
        
        # Update user's avatar in database
        service = UserService(db)
        await service.update_avatar(current_user.id, object_name)
        
        response_data = AvatarUploadResponse(avatar_url=avatar_url)
        
        return success_response(
            data=response_data.model_dump(),
            message="Avatar uploaded successfully",
        )
        
    except BadRequestException as e:
        logger.warning(f"Avatar upload validation failed for user {current_user.id}: {e.message}")
        return success_response(
            data=None,
            message=e.message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        
    except ServiceUnavailableException as e:
        logger.error(f"Avatar upload failed for user {current_user.id}: {e.message}")
        return success_response(
            data=None,
            message="Failed to upload avatar. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during avatar upload for user {current_user.id}: {e}", exc_info=True)
        return success_response(
            data=None,
            message="An unexpected error occurred. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Delete user account"""
    service = UserService(db)
    await service.delete_account(
        current_user.id,
        deletion_request.password,
        deletion_request.confirmation,
    )

    return success_response(
        message="Account deletion initiated. You will receive a confirmation email.",
    )
