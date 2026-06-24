"""Common utilities and helpers"""

from app.common.exceptions import (
    AppException,
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ServiceUnavailableException,
    UnauthorizedException,
    ValidationException,
)
from app.common.logging import get_logger, setup_logging
from app.common.pagination import Paginated, PaginationParams, paginate
from app.common.responses import (
    ErrorResponse,
    PaginatedResponse,
    PaginationMetadata,
    SuccessResponse,
    error_response,
    paginated_response,
    success_response,
)

__all__ = [
    # Exceptions
    "AppException",
    "NotFoundException",
    "BadRequestException",
    "UnauthorizedException",
    "ForbiddenException",
    "ConflictException",
    "ValidationException",
    "ServiceUnavailableException",
    # Responses
    "SuccessResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "PaginationMetadata",
    "success_response",
    "error_response",
    "paginated_response",
    # Pagination
    "Paginated",
    "PaginationParams",
    "paginate",
    # Logging
    "get_logger",
    "setup_logging",
]
