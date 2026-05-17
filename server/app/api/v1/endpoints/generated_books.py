"""Generated Book / Book Generation API Routes"""

import asyncio
import io
import re
from typing import Any
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import PaginationParams, get_logger, paginated_response, success_response
from app.common.exceptions import BadRequestException, ForbiddenException, NotFoundException, ServiceUnavailableException
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


def get_current_user_id() -> UUID:
    """Stub auth — replace with real JWT dependency when auth is wired up."""
    return UUID("00000000-0000-0000-0000-000000000001")


def _parse_child_age(child_age: str | None) -> int | None:
    """Parse age from form payload with user-friendly validation.

    Accepts integer-like strings (e.g. "6", " 7 "). Returns None when omitted.
    """
    if child_age is None:
        return None

    raw = child_age.strip()
    if not raw:
        return None

    try:
        parsed = int(raw)
    except ValueError as exc:
        raise BadRequestException("child_age must be a whole number between 1 and 18") from exc

    if parsed < 1 or parsed > 18:
        raise BadRequestException("child_age must be between 1 and 18")

    return parsed


async def _get_or_create_guest_user(db: AsyncSession, email: str) -> UUID:
    """Look up a user by email, or create a minimal guest account if not found.

    This lets public (unauthenticated) personalized-order submissions be stored
    with a valid user_id foreign key.
    """
    import secrets
    from app.models.user import User
    from sqlalchemy import select as _select

    result = await db.execute(_select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        return user.id

    # Generate a short unique referral code
    referral_code = secrets.token_urlsafe(10)[:12].upper()

    guest = User(
        email=email,
        password_hash=None,
        first_name="Guest",
        last_name="",
        full_name="Guest",
        referral_code=referral_code,
        referral_count=0,
    )
    db.add(guest)
    await db.flush()  # assigns guest.id without committing outer txn
    return guest.id


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


async def process_personalized_uploads(
    photos: list[UploadFile],
    storage_service: StorageService,
    child_name: str | None,
    max_size_mb: int = 10,
) -> tuple[list[str], str]:
    """Upload photos to personalized/{child_name}_{folder_id}/ and return (object_names, folder).

    Uses a stable folder per submission so admin can browse organized folders in MinIO.
    """
    safe_name = re.sub(r"[^a-z0-9]+", "_", (child_name or "child").lower()).strip("_")[:30]
    folder_id = str(uuid4()).replace("-", "")[:12]
    folder = f"personalized/{safe_name}_{folder_id}"

    photo_object_names: list[str] = []
    for idx, photo in enumerate(photos):
        try:
            object_name = await storage_service.upload_personalized_photo(
                file=photo,
                folder=folder,
                index=idx,
                max_size_mb=max_size_mb,
            )
            photo_object_names.append(object_name)
        except Exception as e:
            from app.common.exceptions import BadRequestException as _BE, ServiceUnavailableException as _SE
            if isinstance(e, _BE):
                raise _BE(message=f"Photo {idx + 1} error: {e.message}")  # type: ignore[attr-defined]
            raise _SE(message=f"Failed to upload photo {idx + 1}. Please try again.")

    return photo_object_names, folder


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
    child_age: str | None = Form(None, description="Child age (required if no child_id)"),
    child_gender: str | None = Form(None, description="Child gender (required if no child_id)"),
    parent_email: str = Form(..., description="Parent email required for delivery and notifications"),
    whatsapp_number: str | None = Form(None, description="WhatsApp number for order updates (required for printed copies)"),
    photos: list[UploadFile] = File(..., description="1-3 photos, max 10MB each"),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Initiate book generation process"""
    
    parsed_child_age = _parse_child_age(child_age)

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
        child_age=parsed_child_age,
        child_gender=child_gender,  # type: ignore
        parent_email=parent_email,
        whatsapp_number=whatsapp_number,
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
    child_age: str | None = Form(None, description="Child age (required if no child_id)"),
    child_gender: str | None = Form(None, description="Child gender (required if no child_id)"),
    parent_email: str = Form(..., description="Parent email required for delivery and notifications"),
    whatsapp_number: str | None = Form(None, description="WhatsApp number for order updates (required for printed copies)"),
    template_type: str = Form("coloring_book", description="Requested book type: story_book or coloring_book"),
    selected_theme_name: str | None = Form(None, description="Selected theme name from personalized flow (e.g. Adventure, Princess)"),
    line_weight: str = Form("medium", description="Line weight: thin, medium, thick"),
    detail_level: str = Form("medium", description="Detail level: low, medium, high"),
    simplification_level: str = Form("moderate", description="Simplification: minimal, moderate, high"),
    photos: list[UploadFile] = File(..., description="1-10 photos, max 10MB each"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate coloring book by converting photos directly to line art"""

    parsed_child_age = _parse_child_age(child_age)

    # Resolve user_id from parent_email (look up or create a guest account)
    user_id = await _get_or_create_guest_user(db, parent_email)

    # Validate photos (1-10)
    if not photos or len(photos) < 1:
        raise BadRequestException("At least 1 photo is required")
    
    if len(photos) > 10:
        raise BadRequestException("Maximum 10 photos allowed for photo-to-coloring")
    
    # Upload photos to personalized/{child_name}_{folder_id}/ for organized MinIO storage
    storage_service = StorageService()
    photo_urls, _folder = await process_personalized_uploads(photos, storage_service, child_name)
    
    # Create generation request
    generation_data = PhotoToColoringGenerationCreate(
        child_id=child_id,
        child_name=child_name,
        child_age=parsed_child_age,
        child_gender=child_gender,  # type: ignore
        parent_email=parent_email,
        whatsapp_number=whatsapp_number,
        template_type=template_type,  # type: ignore
        selected_theme_name=selected_theme_name,
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
    child_age: str | None = Form(None, description="Child age (required if no child_id)"),
    child_gender: str | None = Form(None, description="Child gender (required if no child_id)"),
    parent_email: str = Form(..., description="Parent email required for delivery and notifications"),
    whatsapp_number: str | None = Form(None, description="WhatsApp number for order updates (required for printed copies)"),
    photos: list[UploadFile] = File(..., description="Reference photos (min/max based on theme)"),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Generate coloring book using AI based on theme and reference photos"""

    parsed_child_age = _parse_child_age(child_age)
    
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
        child_age=parsed_child_age,
        child_gender=child_gender,  # type: ignore
        parent_email=parent_email,
        whatsapp_number=whatsapp_number,
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


@router.get(
    "/books/{book_id}/download-pdf",
    summary="Download book as PDF",
    description="Generate and stream a PDF of all book pages in order. Book must be completed.",
)
async def download_book_pdf(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> StreamingResponse:
    """
    Build a PDF from all generated page images and stream it to the client.

    Pages are ordered by their page_number. Each Replicate-generated PNG
    is fetched from MinIO and composed into a multi-page PDF using Pillow.
    """
    from datetime import timedelta
    from PIL import Image

    from app.repositories.generated_book import GeneratedBookRepository
    from app.services.generated_book import GeneratedBookService
    from app.services.replicate_generation import ReplicateGenerationService
    import httpx

    # Use service to trigger polling (ensures images are downloaded)
    service = GeneratedBookService(db)
    book_details = await service.get_book_details(book_id, user_id)
    
    # Now fetch the raw book model with updated data
    repo = GeneratedBookRepository(db)
    book = await repo.get_by_id(book_id, user_id)

    if not book:
        raise NotFoundException("Book not found")

    if book.status != "completed":
        raise BadRequestException("Book is not ready for download yet")

    prediction_map: dict = book.replicate_prediction_ids or {}
    
    logger.info(
        "download_pdf_request",
        book_id=str(book_id),
        status=book.status,
        prediction_map_keys=list(prediction_map.keys()) if prediction_map else [],
        has_prediction_map=bool(prediction_map),
    )
    
    if not prediction_map:
        raise BadRequestException("No generated images found for this book")

    # Sort pages by page_number
    sorted_pages = sorted(
        prediction_map.items(),
        key=lambda x: x[1].get("page_number", 0),
    )

    storage = StorageService()

    # Collect all page images in order
    pil_images: list[Image.Image] = []
    async with httpx.AsyncClient(timeout=60) as client:
        for _key, info in sorted_pages:
            image_object = info.get("image_object")
            logger.info(
                "processing_pdf_page",
                book_id=str(book_id),
                key=_key,
                has_image_object=bool(image_object),
                info_keys=list(info.keys()),
                status=info.get("status"),
            )
            if not image_object:
                logger.warning(
                    "pdf_page_missing_image_object",
                    book_id=str(book_id),
                    key=_key,
                    info=info,
                )
                continue
            try:
                presigned_url = await storage.get_file_url(
                    image_object, expires=timedelta(minutes=10)
                )
                resp = await client.get(presigned_url)
                resp.raise_for_status()
                img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                pil_images.append(img)
                logger.info(
                    "pdf_page_loaded",
                    book_id=str(book_id),
                    key=_key,
                    image_size=img.size,
                )
            except Exception as exc:
                logger.warning(
                    "pdf_page_fetch_failed",
                    book_id=str(book_id),
                    object_name=image_object,
                    error=str(exc),
                )

    if not pil_images:
        raise ServiceUnavailableException("Could not load any page images")

    # Build PDF in memory
    pdf_buffer = io.BytesIO()
    pil_images[0].save(
        pdf_buffer,
        format="PDF",
        save_all=True,
        append_images=pil_images[1:],
    )
    pdf_buffer.seek(0)

    safe_title = (book.child_name or "book").replace(" ", "_")
    filename = f"{safe_title}_storybook.pdf"

    return StreamingResponse(
        content=pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
