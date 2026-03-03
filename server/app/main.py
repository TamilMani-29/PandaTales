"""Main FastAPI Application"""

import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.common import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
    error_response,
    get_logger,
    setup_logging,
    success_response,
)
from app.core.config import get_settings
from app.db.session import close_db, init_db

# Setup logging
setup_logging()
logger = get_logger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager"""
    logger.info("application_starting", environment=settings.APP_ENV)

    # Initialize database
    await init_db()
    logger.info("database_initialized")

    yield

    # Cleanup
    logger.info("application_shutting_down")
    await close_db()
    logger.info("database_connections_closed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="PandaTales - AI-Powered Children's Coloring Book Generation Platform",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    openapi_url="/openapi.json" if settings.APP_ENV != "production" else None,
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing"""
    start_time = time.time()

    # Log request
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else None,
    )

    try:
        response = await call_next(request)

        # Log response
        duration = time.time() - start_time
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )

        return response

    except Exception as exc:
        duration = time.time() - start_time
        logger.error(
            "request_failed",
            method=request.method,
            path=request.url.path,
            error=str(exc),
            duration_ms=round(duration * 1000, 2),
            exc_info=True,
        )
        raise


# Exception Handlers
@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    """Handle not found exceptions"""
    logger.warning(
        "not_found",
        path=request.url.path,
        detail=exc.detail,
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error_response(exc.detail, status.HTTP_404_NOT_FOUND),
    )


@app.exception_handler(BadRequestException)
async def bad_request_exception_handler(request: Request, exc: BadRequestException):
    """Handle bad request exceptions"""
    logger.warning(
        "bad_request",
        path=request.url.path,
        detail=exc.detail,
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response(exc.detail, status.HTTP_400_BAD_REQUEST),
    )


@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    """Handle unauthorized exceptions"""
    logger.warning(
        "unauthorized",
        path=request.url.path,
        detail=exc.detail,
    )
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error_response(exc.detail, status.HTTP_401_UNAUTHORIZED),
    )


@app.exception_handler(ForbiddenException)
async def forbidden_exception_handler(request: Request, exc: ForbiddenException):
    """Handle forbidden exceptions"""
    logger.warning(
        "forbidden",
        path=request.url.path,
        detail=exc.detail,
    )
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=error_response(exc.detail, status.HTTP_403_FORBIDDEN),
    )


@app.exception_handler(ConflictException)
async def conflict_exception_handler(request: Request, exc: ConflictException):
    """Handle conflict exceptions"""
    logger.warning(
        "conflict",
        path=request.url.path,
        detail=exc.detail,
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=error_response(exc.detail, status.HTTP_409_CONFLICT),
    )


@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """Handle validation exceptions"""
    logger.warning(
        "validation_error",
        path=request.url.path,
        detail=exc.detail,
        errors=exc.errors,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            message=exc.detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            errors=exc.errors,
        ),
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(
        "request_validation_error",
        path=request.url.path,
        errors=errors,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            message="Validation error",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            errors=errors,
        ),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            code="INTERNAL_ERROR",
            message="Internal server error",
        ),
    )


# Health Check
@app.get(
    "/health",
    tags=["Health"],
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if the API is running",
)
async def health_check():
    """Health check endpoint"""
    return success_response(
        data={
            "status": "healthy",
            "environment": settings.APP_ENV,
            "version": "1.0.0",
        },
        message="API is running",
    )


# Include API routers
app.include_router(api_router, prefix="/api")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to PandaTales API",
        "docs": "/docs",
        "health": "/health",
    }


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.APP_ENV != "production",
        log_level="info",
    )
