"""Address Service - Business Logic Layer"""

from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.logging import get_logger
from app.models.address import Address
from app.repositories.address import AddressRepository
from app.schemas.user import AddressCreate, AddressUpdate

logger = get_logger(__name__)


class AddressService:
    """Service for address business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = AddressRepository(db)

    async def get_address(self, address_id: UUID, user_id: UUID) -> Address:
        """Get address by ID"""
        logger.info("fetching_address", address_id=str(address_id), user_id=str(user_id))
        return await self.repository.get_by_id(address_id, user_id=user_id)

    async def list_addresses(self, user_id: UUID) -> Sequence[Address]:
        """List all addresses for a user"""
        logger.info("listing_addresses", user_id=str(user_id))
        addresses = await self.repository.get_all_by_user(user_id)
        logger.info("addresses_listed", user_id=str(user_id), count=len(addresses))
        return addresses

    async def create_address(
        self, user_id: UUID, address_data: AddressCreate
    ) -> Address:
        """Create a new address"""
        logger.info("creating_address", user_id=str(user_id), city=address_data.city, country=address_data.country)
        address = await self.repository.create(user_id, address_data)
        logger.info("address_created", address_id=str(address.id), user_id=str(user_id))
        return address

    async def update_address(
        self, address_id: UUID, user_id: UUID, address_data: AddressUpdate
    ) -> Address:
        """Update an address"""
        logger.info("updating_address", address_id=str(address_id), user_id=str(user_id))
        address = await self.repository.update(address_id, user_id, address_data)
        logger.info("address_updated", address_id=str(address.id), user_id=str(user_id))
        return address

    async def delete_address(self, address_id: UUID, user_id: UUID) -> None:
        """Delete an address"""
        logger.info("deleting_address", address_id=str(address_id), user_id=str(user_id))
        await self.repository.delete(address_id, user_id)
        logger.info("address_deleted", address_id=str(address_id), user_id=str(user_id))

    async def set_default_address(self, address_id: UUID, user_id: UUID) -> Address:
        """Set an address as default"""
        logger.info("setting_default_address", address_id=str(address_id), user_id=str(user_id))
        address = await self.repository.set_as_default(address_id, user_id)
        logger.info("default_address_set", address_id=str(address.id), user_id=str(user_id))
        return address
