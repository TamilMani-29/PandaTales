"""Standard API Response Models"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response"""

    success: bool = True
    message: str = "Success"
    data: T | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Success",
                "data": {"id": "123", "name": "Example"},
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""

    success: bool = False
    error: dict[str, Any] = Field(
        ...,
        description="Error details",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Resource not found",
                    "details": {},
                },
            }
        }


class PaginationMetadata(BaseModel):
    """Pagination metadata"""

    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response"""

    success: bool = True
    message: str = "Success"
    data: list[T]
    pagination: PaginationMetadata

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Success",
                "data": [{"id": "123", "name": "Item 1"}],
                "pagination": {
                    "page": 1,
                    "limit": 20,
                    "total": 50,
                    "pages": 3,
                    "has_next": True,
                    "has_prev": False,
                },
            }
        }


def success_response(
    data: Any = None,
    message: str = "Success",
) -> dict[str, Any]:
    """Create a success response"""
    return {"success": True, "message": message, "data": data}


def error_response(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create an error response"""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
    }


def paginated_response(
    data: list[Any],
    page: int,
    limit: int,
    total: int,
    message: str = "Success",
) -> dict[str, Any]:
    """Create a paginated response"""
    pages = (total + limit - 1) // limit  # Ceiling division

    return {
        "success": True,
        "message": message,
        "data": data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1,
        },
    }
