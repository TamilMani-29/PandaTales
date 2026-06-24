"""Address Repository - Data Access Layer"""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ForbiddenException, NotFoundException
from app.models.address import Address
from app.schemas.user import AddressCreate, AddressUpdate


class AddressRepository:
    """Repository for address data access"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self, address_id: UUID, user_id: UUID | None = None, include_inactive: bool = False
    ) -> Address:
        """Get address by ID"""
        query = select(Address).where(Address.id == address_id)

        if user_id:
            query = query.where(Address.user_id == user_id)

        if not include_inactive:
            query = query.where(Address.is_active == True)

        result = await self.db.execute(query)
        address = result.scalar_one_or_none()

        if not address:
            raise NotFoundException(
                message="Address not found",
                error_code="ADDRESS_NOT_FOUND",
                details={"address_id": str(address_id)},
            )

        # Check ownership if user_id provided
        if user_id and address.user_id != user_id:
            raise ForbiddenException(
                message="Not authorized to access this address",
                error_code="UNAUTHORIZED_ACCESS",
            )

        return address

    async def get_all_by_user(
        self, user_id: UUID, include_inactive: bool = False
    ) -> Sequence[Address]:
        """Get all addresses for a user"""
        query = select(Address).where(Address.user_id == user_id)

        if not include_inactive:
            query = query.where(Address.is_active == True)

        # Order by: default first, then by creation date
        query = query.order_by(Address.is_default.desc(), Address.created_at.desc())

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_default_address(self, user_id: UUID) -> Address | None:
        """Get user's default address"""
        query = select(Address).where(
            Address.user_id == user_id,
            Address.is_default == True,
            Address.is_active == True,
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, user_id: UUID, address_data: AddressCreate) -> Address:
        """Create a new address"""
        # If this is set as default, unset current default
        if address_data.is_default:
            await self._unset_default(user_id)

        address = Address(
            user_id=user_id,
            **address_data.model_dump(),
        )
        self.db.add(address)
        await self.db.commit()
        await self.db.refresh(address)
        return address

    async def update(
        self, address_id: UUID, user_id: UUID, address_data: AddressUpdate
    ) -> Address:
        """Update an address"""
        address = await self.get_by_id(address_id, user_id=user_id, include_inactive=True)

        # If setting as default, unset current default
        update_data = address_data.model_dump(exclude_unset=True)
        if update_data.get("is_default", False):
            await self._unset_default(user_id)

        # Update only provided fields
        for field, value in update_data.items():
            setattr(address, field, value)

        await self.db.commit()
        await self.db.refresh(address)
        return address

    async def delete(self, address_id: UUID, user_id: UUID) -> None:
        """Soft delete an address"""
        address = await self.get_by_id(address_id, user_id=user_id, include_inactive=True)
        address.is_active = False
        await self.db.commit()

    async def _unset_default(self, user_id: UUID) -> None:
        """Unset current default address for user"""
        current_default = await self.get_default_address(user_id)
        if current_default:
            current_default.is_default = False
            await self.db.commit()

    async def set_as_default(self, address_id: UUID, user_id: UUID) -> Address:
        """Set an address as default"""
        # Unset current default
        await self._unset_default(user_id)

        # Set new default
        address = await self.get_by_id(address_id, user_id=user_id)
        address.is_default = True
        await self.db.commit()
        await self.db.refresh(address)
        return address
