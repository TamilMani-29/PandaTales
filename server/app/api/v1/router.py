"""API v1 Router"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    addresses,
    admin,
    auth,
    checkout,
    children,
    coloring_books,
    digital_books,
    generated_books,
    generation_configs,
    payments,
    story_books,
    users,
)

api_router = APIRouter(prefix="/v1")

# Include routers
api_router.include_router(story_books.router)
api_router.include_router(coloring_books.router)
api_router.include_router(digital_books.router)
api_router.include_router(payments.router)
api_router.include_router(admin.router)
api_router.include_router(auth.router)
api_router.include_router(generated_books.router)
api_router.include_router(checkout.router)
api_router.include_router(generation_configs.public_router)  # Public themes endpoint
api_router.include_router(generation_configs.admin_router)  # Admin config endpoints
api_router.include_router(users.router)
api_router.include_router(children.router)
api_router.include_router(addresses.router)

# TODO: Add other module routers as they're developed
