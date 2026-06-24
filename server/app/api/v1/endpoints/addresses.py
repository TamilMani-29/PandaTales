"""Address API Routes"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import get_logger, success_response
from app.db.session import get_db
from app.schemas.user import (
    AddressCreate,
    AddressListResponse,
    AddressResponse,
    AddressUpdate,
)
from app.services.address import AddressService

logger = get_logger(__name__)

router = APIRouter(prefix="/users/addresses", tags=["Addresses"])


# TODO: Add authentication dependency
def get_current_user_id() -> UUID:
    """Temporary function to get current user ID - replace with actual auth"""
    return UUID("00000000-0000-0000-0000-000000000001")


@router.get(
    "",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="List addresses",
    description="Get all saved addresses for the authenticated user",
)
async def list_addresses(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List addresses"""
    service = AddressService(db)
    addresses = await service.list_addresses(user_id)

    addresses_data = [AddressResponse.model_validate(addr) for addr in addresses]
    response = AddressListResponse(
        addresses=addresses_data,
        total_count=len(addresses_data),
    )

    return success_response(
        data=response.model_dump(),
        message="Addresses retrieved successfully",
    )


@router.post(
    "",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create address",
    description="Add a new shipping address",
)
async def create_address(
    address_data: AddressCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create address"""
    service = AddressService(db)
    address = await service.create_address(user_id, address_data)

    response_data = AddressResponse.model_validate(address)

    return success_response(
        data=response_data.model_dump(),
        message="Address added successfully",
    )


@router.get(
    "/{address_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get address",
    description="Get details of a specific address",
)
async def get_address(
    address_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get address"""
    service = AddressService(db)
    address = await service.get_address(address_id, user_id)

    response_data = AddressResponse.model_validate(address)

    return success_response(
        data=response_data.model_dump(),
        message="Address retrieved successfully",
    )


@router.patch(
    "/{address_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Update address",
    description="Update a shipping address",
)
async def update_address(
    address_id: UUID,
    address_data: AddressUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update address"""
    service = AddressService(db)
    address = await service.update_address(address_id, user_id, address_data)

    response_data = AddressResponse.model_validate(address)

    return success_response(
        data=response_data.model_dump(),
        message="Address updated successfully",
    )


@router.delete(
    "/{address_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Delete address",
    description="Delete a shipping address",
)
async def delete_address(
    address_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Delete address"""
    service = AddressService(db)
    await service.delete_address(address_id, user_id)

    return success_response(
        message="Address deleted successfully",
    )


@router.post(
    "/{address_id}/set-default",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Set default address",
    description="Set an address as the default shipping address",
)
async def set_default_address(
    address_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Set address as default"""
    service = AddressService(db)
    address = await service.set_default_address(address_id, user_id)

    response_data = AddressResponse.model_validate(address)

    return success_response(
        data=response_data.model_dump(),
        message="Default address updated successfully",
    )
