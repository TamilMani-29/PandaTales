"""Generated Book / Book Generation API Routes"""

from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import PaginationParams, get_logger, paginated_response, success_response
from app.common.exceptions import BadRequestException, ServiceUnavailableException
from app.db.session import get_db
from app.schemas.generated_book import (
    BookGenerationCreate,
    BookGenerationResponse,
    GeneratedBookFilters,
    GeneratedBookListItem,
    GeneratedBookResponse,
    PhotoToColoringGenerationCreate,
    ThemeBasedGenerationCreate,
)
from app.services.generated_book import GeneratedBookService
from app.services.storage import StorageService

logger = get_logger(__name__)

router = APIRouter(tags=["Book Generation"])


# TODO: Replace with real JWT auth dependency
def get_current_user_id() -> UUID:
    """Temporary function to get current user ID - replace with actual auth"""
    return UUID("00000000-0000-0000-0000-000000000001")


# Helper function to handle photo uploads with MinIO storage
async def process_photo_uploads(
    photos: list[UploadFile],
    storage_service: StorageService,
    max_size_mb: int = 10,
) -> list[str]:
    """Process and upload photos to MinIO, return object names"""
    photo_urls = []
    
    for idx, photo in enumerate(photos):
        try:
            # Upload each photo with validation
            object_name = await storage_service.upload_image(
                file=photo,
                prefix="photos",
                max_size_mb=max_size_mb,
            )
            photo_urls.append(object_name)
            
        except BadRequestException as e:
            # Re-raise with more context
            raise BadRequestException(
                message=f"Photo {idx + 1} error: {e.message}"
            )
        except ServiceUnavailableException as e:
            logger.error(f"Failed to upload photo {idx + 1}: {e.message}", exc_info=True)
            raise ServiceUnavailableException(
                message=f"Failed to upload photo {idx + 1}. Please try again."
            )
        except Exception as e:
            logger.error(f"Unexpected error uploading photo {idx + 1}: {e}", exc_info=True)
            raise ServiceUnavailableException(
                message=f"Failed to upload photo {idx + 1}. Please try again."
            )
    
    return photo_urls


@router.post(
    "/books/generate",
    response_model=dict[str, Any],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate book generation",
    description="Start the personalized book generation process",
)
async def initiate_book_generation(
    template_id: UUID = Form(..., description="Template ID"),
    template_type: str = Form(..., description="Template type: story_book or coloring_book"),
    child_id: UUID | None = Form(None, description="Child profile ID (optional)"),
    child_name: str | None = Form(None, description="Child name (required if no child_id)"),
    child_age: int | None = Form(None, description="Child age (required if no child_id)"),
    child_gender: str | None = Form(None, description="Child gender (required if no child_id)"),
    parent_email: str | None = Form(None, description="Parent email for notifications"),
    photos: list[UploadFile] = File(..., description="1-3 photos, max 10MB each"),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Initiate book generation process"""
    
    # Validate photos
    if not photos or len(photos) < 1:
        raise BadRequestException("At least 1 photo is required")
    
    if len(photos) > 3:
        raise BadRequestException("Maximum 3 photos allowed")
    
    # Process photo uploads with proper error handling
    storage_service = StorageService()
    photo_urls = await process_photo_uploads(photos, storage_service)
    
    # Create generation request
    generation_data = BookGenerationCreate(
        template_id=template_id,
        template_type=template_type,  # type: ignore
        child_id=child_id,
        child_name=child_name,
        child_age=child_age,
        child_gender=child_gender,  # type: ignore
        parent_email=parent_email,
    )
    
    service = GeneratedBookService(db)
    result = await service.initiate_generation(user_id, generation_data, photo_urls)
    
    return success_response(
        data=result.model_dump(),
        message="Book generation started",
    )


@router.post(
    "/books/generate/photo-to-coloring",
    response_model=dict[str, Any],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate photo-to-coloring book",
    description="Convert uploaded photos directly to coloring pages (1-10 photos)",
)
async def generate_photo_to_coloring_book(
    child_id: UUID | None = Form(None, description="Child profile ID (optional)"),
    child_name: str | None = Form(None, description="Child name (required if no child_id)"),
    child_age: int | None = Form(None, description="Child age (required if no child_id)"),
    child_gender: str | None = Form(None, description="Child gender (required if no child_id)"),
    parent_email: str | None = Form(None, description="Parent email for notifications"),
    line_weight: str = Form("medium", description="Line weight: thin, medium, thick"),
    detail_level: str = Form("medium", description="Detail level: low, medium, high"),
    simplification_level: str = Form("moderate", description="Simplification: minimal, moderate, high"),
    photos: list[UploadFile] = File(..., description="1-10 photos, max 10MB each"),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Generate coloring book by converting photos directly to line art"""
    
    # Validate photos (1-10)
    if not photos or len(photos) < 1:
        raise BadRequestException("At least 1 photo is required")
    
    if len(photos) > 10:
        raise BadRequestException("Maximum 10 photos allowed for photo-to-coloring")
    
    # Process photo uploads with proper error handling
    storage_service = StorageService()
    photo_urls = await process_photo_uploads(photos, storage_service)
    
    # Create generation request
    generation_data = PhotoToColoringGenerationCreate(
        child_id=child_id,
        child_name=child_name,
        child_age=child_age,
        child_gender=child_gender,  # type: ignore
        parent_email=parent_email,
        line_weight=line_weight,  # type: ignore
        detail_level=detail_level,  # type: ignore
        simplification_level=simplification_level,  # type: ignore
    )
    
    service = GeneratedBookService(db)
    result = await service.initiate_photo_to_coloring_generation(
        user_id, generation_data, photo_urls
    )
    
    return success_response(
        data=result.model_dump(),
        message="Photo-to-coloring generation started",
    )


@router.post(
    "/books/generate/theme-based",
    response_model=dict[str, Any],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate theme-based coloring book",
    description="Generate AI coloring pages based on selected theme and reference photos",
)
async def generate_theme_based_coloring_book(
    theme_config_id: UUID = Form(..., description="Theme configuration ID"),
    num_pages: int = Form(..., ge=5, le=30, description="Number of pages (5-30)"),
    coloring_style: str = Form("simple", description="Style: simple, detailed, mandala, cartoon"),
    child_id: UUID | None = Form(None, description="Child profile ID (optional)"),
    child_name: str | None = Form(None, description="Child name (required if no child_id)"),
    child_age: int | None = Form(None, description="Child age (required if no child_id)"),
    child_gender: str | None = Form(None, description="Child gender (required if no child_id)"),
    parent_email: str | None = Form(None, description="Parent email for notifications"),
    photos: list[UploadFile] = File(..., description="Reference photos (min/max based on theme)"),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Generate coloring book using AI based on theme and reference photos"""
    
    # Note: Photo count validation happens in service layer based on theme config
    if not photos or len(photos) < 1:
        raise BadRequestException("At least 1 photo is required")
    
    # Process photo uploads with proper error handling
    storage_service = StorageService()
    photo_urls = await process_photo_uploads(photos, storage_service)
    
    # Create generation request
    generation_data = ThemeBasedGenerationCreate(
        theme_config_id=theme_config_id,
        num_pages=num_pages,
        coloring_style=coloring_style,  # type: ignore
        child_id=child_id,
        child_name=child_name,
        child_age=child_age,
        child_gender=child_gender,  # type: ignore
        parent_email=parent_email,
    )
    
    service = GeneratedBookService(db)
    
    # Service will validate photo count against theme config
    try:
        result = await service.initiate_theme_based_generation(
            user_id, generation_data, photo_urls
        )
    except ValueError as e:
        raise BadRequestException(str(e))
    
    return success_response(
        data=result.model_dump(),
        message="Theme-based generation started",
    )


@router.get(
    "/books/generate/{generation_id}/status",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get generation status",
    description="Get current status of book generation process",
)
async def get_generation_status(
    generation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Get generation status"""
    service = GeneratedBookService(db)
    status_data = await service.get_generation_status(generation_id, user_id)
    
    return success_response(
        data=status_data.model_dump(),
        message="Generation status retrieved",
    )


@router.delete(
    "/books/generate/{generation_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Cancel generation",
    description="Cancel a queued or in-progress generation",
)
async def cancel_generation(
    generation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Cancel generation"""
    service = GeneratedBookService(db)
    await service.cancel_generation(generation_id, user_id)
    
    return success_response(
        data=None,
        message="Generation cancelled successfully",
    )


@router.get(
    "/books/generated",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="List generated books",
    description="Get all books generated by the user",
)
async def list_generated_books(
    # Pagination
    pagination: PaginationParams = Depends(),
    # Filters
    child_id: UUID | None = Query(None, description="Filter by child profile"),
    template_type: str | None = Query(None, description="Filter by template type"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    is_purchased: bool | None = Query(None, description="Filter by purchase status"),
    sort: str = Query("newest", description="Sort by: newest, oldest, title"),
    # Dependencies
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """List user's generated books"""
    
    filters = GeneratedBookFilters(
        child_id=child_id,
        template_type=template_type,  # type: ignore
        status=status_filter,  # type: ignore
        is_purchased=is_purchased,
        sort=sort,  # type: ignore
    )
    
    service = GeneratedBookService(db)
    items, total = await service.list_generated_books(user_id, filters, pagination)
    
    return paginated_response(
        items=[item.model_dump() for item in items],
        total=total,
        pagination=pagination,
    )


@router.get(
    "/books/{book_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get book details",
    description="Get details of a specific generated book",
)
async def get_book_details(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Get generated book details"""
    service = GeneratedBookService(db)
    book = await service.get_book_details(book_id, user_id)
    
    return success_response(
        data=book.model_dump(),
        message="Book details retrieved",
    )


@router.delete(
    "/books/{book_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Delete book",
    description="Delete a generated book (only unpurchased books)",
)
async def delete_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Delete a generated book"""
    service = GeneratedBookService(db)
    await service.delete_book(book_id, user_id)
    
    return success_response(
        data=None,
        message="Book deleted successfully",
    )


@router.post(
    "/books/{book_id}/regenerate",
    response_model=dict[str, Any],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Regenerate book",
    description="Regenerate a book with the same parameters",
)
async def regenerate_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Regenerate a book"""
    service = GeneratedBookService(db)
    result = await service.regenerate_book(book_id, user_id)
    
    return success_response(
        data=result.model_dump(),
        message="Book regeneration started",
        status_code=status.HTTP_202_ACCEPTED,
    )
