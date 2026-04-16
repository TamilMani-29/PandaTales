"""Digital books catalog API routes."""

from typing import Any

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import success_response
from app.core.constants import AgeGroup, BookType, Language, Style, Theme
from app.db.session import get_db
from app.schemas.digital_book import DigitalBookCreateRequest, SendPdfEmailRequest
from app.services.digital_book import DigitalBookService

router = APIRouter(prefix="/digital-books", tags=["Digital Books"])


@router.post(
    "",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create a digital book",
    description="Create digital book metadata, upload cover/PDF to MinIO, and save URLs in DB.",
)
async def create_digital_book(
    book_name: str = Form(..., min_length=1, max_length=255),
    description: str | None = Form(None),
    total_pages: int | None = Form(None, ge=1),
    book_type: BookType = Form(...),
    theme: Theme = Form(...),
    style: Style = Form(...),
    age_group: AgeGroup = Form(...),
    language: Language = Form(Language.ENGLISH),
    genre: str = Form(..., min_length=1, max_length=100),
    price: float | None = Form(None, ge=0),
    cover_image: UploadFile = File(...),
    book_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new digital book entry and upload assets."""
    payload = DigitalBookCreateRequest(
        book_name=book_name,
        description=description,
        total_pages=total_pages,
        book_type=book_type,
        theme=theme,
        style=style,
        age_group=age_group,
        language=language,
        genre=genre,
        price=price,
    )

    service = DigitalBookService(db)
    book = await service.create_book(payload, cover_image=cover_image, book_file=book_file)
    created_data = await service.get_book(book.id)

    return success_response(
        data=created_data,
        message="Digital book created successfully",
    )


@router.get(
    "",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get digital books",
    description="Return digital books with optional search and filters. PDF URL is excluded.",
)
async def get_digital_books(
    search: str | None = Query(None, max_length=120),
    book_type: BookType | None = Query(None),
    genre: str | None = Query(None, max_length=100),
    style: Style | None = Query(None),
    age_group: AgeGroup | None = Query(None),
    language: Language | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    limit: int = Query(60, ge=1, le=120),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get digital books with optional search/filter support."""
    service = DigitalBookService(db)

    data = await service.list_books(
        search=search,
        book_type=book_type,
        genre=genre,
        style=style,
        age_group=age_group,
        language=language,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
        offset=offset,
    )
    return success_response(data=data, message="Digital books retrieved successfully")


@router.get(
    "/filter-options",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get digital book filter options",
    description="Get available filter values for digital books page.",
)
async def get_digital_book_filter_options(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Get available filters for digital books UI."""
    service = DigitalBookService(db)
    data = await service.get_filter_options()
    return success_response(data=data, message="Digital book filters retrieved successfully")


@router.get(
    "/{book_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get digital book details",
    description="Get one digital book by ID with full metadata and presigned cover image.",
)
async def get_digital_book_by_id(book_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Get one digital book by ID."""
    service = DigitalBookService(db)
    data = await service.get_book(book_id)
    return success_response(data=data, message="Digital book retrieved successfully")


@router.post(
    "/send-pdf-email",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Send book PDF to email",
    description="Send selected book's PDF as an email attachment to provided email address.",
)
async def send_book_pdf_to_email(
    request: SendPdfEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Send book PDF to the requested email address."""
    service = DigitalBookService(db)
    await service.send_pdf_to_email(book_id=request.book_id, recipient_email=str(request.email))

    return success_response(
        data={"book_id": request.book_id, "email": str(request.email)},
        message="Successfully email sent",
    )
