"""API v1 Router"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    addresses,
    checkout,
    children,
    coloring_books,
    generated_books,
    generation_configs,
    # story_books,  # Commented out - not included in this release
    users,
)

api_router = APIRouter(prefix="/v1")

# Include routers
# api_router.include_router(story_books.router)  # Commented out - not included in this release
api_router.include_router(coloring_books.router)
api_router.include_router(generated_books.router)
api_router.include_router(checkout.router)
api_router.include_router(generation_configs.public_router)  # Public themes endpoint
api_router.include_router(generation_configs.admin_router)  # Admin config endpoints
api_router.include_router(users.router)
api_router.include_router(children.router)
api_router.include_router(addresses.router)

# TODO: Add other module routers as they're developed
# api_router.include_router(auth.router)
