"""Child Profile API Routes"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import get_logger, success_response
from app.db.session import get_db
from app.schemas.user import (
    ChildProfileCreate,
    ChildProfileListResponse,
    ChildProfileResponse,
    ChildProfileUpdate,
)
from app.services.child_profile import ChildProfileService

logger = get_logger(__name__)

router = APIRouter(prefix="/users/children", tags=["Child Profiles"])


# TODO: Add authentication dependency
def get_current_user_id() -> UUID:
    """Temporary function to get current user ID - replace with actual auth"""
    return UUID("00000000-0000-0000-0000-000000000001")


@router.get(
    "",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="List child profiles",
    description="Get all child profiles for the authenticated user",
)
async def list_children(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List child profiles"""
    service = ChildProfileService(db)
    children = await service.list_children(user_id)

    children_data = [ChildProfileResponse.model_validate(child) for child in children]
    response = ChildProfileListResponse(
        children=children_data,
        total_count=len(children_data),
    )

    return success_response(
        data=response.model_dump(),
        message="Child profiles retrieved successfully",
    )


@router.post(
    "",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create child profile",
    description="Create a new child profile",
)
async def create_child_profile(
    child_data: ChildProfileCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create child profile"""
    service = ChildProfileService(db)
    child = await service.create_child_profile(user_id, child_data)

    response_data = ChildProfileResponse.model_validate(child)

    return success_response(
        data=response_data.model_dump(),
        message="Child profile created successfully",
    )


@router.get(
    "/{child_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get child profile",
    description="Get details of a specific child profile",
)
async def get_child_profile(
    child_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get child profile"""
    service = ChildProfileService(db)
    child = await service.get_child_profile(child_id, user_id)

    response_data = ChildProfileResponse.model_validate(child)

    return success_response(
        data=response_data.model_dump(),
        message="Child profile retrieved successfully",
    )


@router.patch(
    "/{child_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Update child profile",
    description="Update child profile information",
)
async def update_child_profile(
    child_id: UUID,
    child_data: ChildProfileUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update child profile"""
    service = ChildProfileService(db)
    child = await service.update_child_profile(child_id, user_id, child_data)

    response_data = ChildProfileResponse.model_validate(child)

    return success_response(
        data=response_data.model_dump(),
        message="Child profile updated successfully",
    )


@router.delete(
    "/{child_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Delete child profile",
    description="Delete a child profile (soft delete)",
)
async def delete_child_profile(
    child_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Delete child profile"""
    service = ChildProfileService(db)
    await service.delete_child_profile(child_id, user_id)

    return success_response(
        message="Child profile deleted successfully",
    )
