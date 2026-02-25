"""API v1 Router"""

from fastapi import APIRouter

from app.api.v1.endpoints import addresses, children, templates, users

api_router = APIRouter(prefix="/v1")

# Include routers
api_router.include_router(templates.router)
api_router.include_router(users.router)
api_router.include_router(children.router)
api_router.include_router(addresses.router)

# TODO: Add other module routers as they're developed
# api_router.include_router(auth.router)
# api_router.include_router(generation.router)
