"""Address Service - Business Logic Layer"""

from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address
from app.repositories.address import AddressRepository
from app.schemas.user import AddressCreate, AddressUpdate


class AddressService:
    """Service for address business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = AddressRepository(db)

    async def get_address(self, address_id: UUID, user_id: UUID) -> Address:
        """Get address by ID"""
        return await self.repository.get_by_id(address_id, user_id=user_id)

    async def list_addresses(self, user_id: UUID) -> Sequence[Address]:
        """List all addresses for a user"""
        return await self.repository.get_all_by_user(user_id)

    async def create_address(
        self, user_id: UUID, address_data: AddressCreate
    ) -> Address:
        """Create a new address"""
        return await self.repository.create(user_id, address_data)

    async def update_address(
        self, address_id: UUID, user_id: UUID, address_data: AddressUpdate
    ) -> Address:
        """Update an address"""
        return await self.repository.update(address_id, user_id, address_data)

    async def delete_address(self, address_id: UUID, user_id: UUID) -> None:
        """Delete an address"""
        await self.repository.delete(address_id, user_id)

    async def set_default_address(self, address_id: UUID, user_id: UUID) -> Address:
        """Set an address as default"""
        return await self.repository.set_as_default(address_id, user_id)
