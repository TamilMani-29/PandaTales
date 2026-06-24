"""Digital books catalog API routes."""

import mimetypes
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import success_response
from app.common.exceptions import NotFoundException
from app.db.session import get_db
from app.schemas.digital_book import (
    BookAttributeOptionCreateRequest,
    BookCategoryCreateRequest,
    DigitalBookCreateRequest,
    DigitalBookUpdateRequest,
)
from app.services.digital_book import DigitalBookService
from app.services.storage import StorageService

router = APIRouter(prefix="/digital-books", tags=["Digital Books"])


@router.post(
    "",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create a digital book",
    description="Create digital book metadata, upload cover/front/back images and PDF to Cloudflare R2, and save URLs in DB.",
)
async def create_digital_book(
    book_name: str = Form(..., min_length=1, max_length=255),
    description: str | None = Form(None),
    category_id: int | None = Form(None, ge=1),
    emoji: str | None = Form(None, max_length=16),
    age_group: str | None = Form(None, max_length=32),
    total_pages: int | None = Form(None, ge=1),
    book_type: str = Form(..., min_length=1, max_length=50),
    style: str = Form(..., min_length=1, max_length=50),
    language: str = Form("english", min_length=1, max_length=50),
    genre: str = Form(..., min_length=1, max_length=100),
    price: float | None = Form(None, ge=0),
    rating: float | None = Form(None, ge=0, le=5),
    total_ratings: int | None = Form(None, ge=0),
    download_count: int | None = Form(None, ge=0),
    is_bestseller: bool = Form(False),
    is_personalized: bool = Form(False),
    cover_image: UploadFile = File(...),
    front_image: UploadFile | None = File(None),
    back_image: UploadFile | None = File(None),
    page_1_image: UploadFile | None = File(None),
    page_2_image: UploadFile | None = File(None),
    page_3_image: UploadFile | None = File(None),
    page_4_image: UploadFile | None = File(None),
    book_file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new digital book entry and upload assets."""
    payload = DigitalBookCreateRequest(
        book_name=book_name,
        description=description,
        category_id=category_id,
        emoji=emoji,
        age_group=age_group,
        total_pages=total_pages,
        book_type=book_type,
        style=style,
        language=language,
        genre=genre,
        price=price,
        rating=rating,
        total_ratings=total_ratings,
        download_count=download_count,
        is_bestseller=is_bestseller,
        is_personalized=is_personalized,
    )

    service = DigitalBookService(db)
    book = await service.create_book(
        payload,
        cover_image=cover_image,
        front_image=front_image,
        back_image=back_image,
        page_1_image=page_1_image,
        page_2_image=page_2_image,
        page_3_image=page_3_image,
        page_4_image=page_4_image,
        book_file=book_file,
    )
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
    book_type: str | None = Query(None, max_length=50),
    genre: str | None = Query(None, max_length=100),
    category_id: int | None = Query(None, ge=1, description="Filter by category id"),
    is_bestseller: bool | None = Query(None, description="Filter bestsellers only"),
    language: str | None = Query(None, max_length=50),
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
        category_id=category_id,
        is_bestseller=is_bestseller,
        language=language,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
        offset=offset,
    )
    return success_response(data=data, message="Digital books retrieved successfully")


@router.get(
    "/categories",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get digital book categories",
    description="List category metadata (name, tag, description, emoji, color, gradient).",
)
async def get_digital_book_categories(
    active_only: bool = Query(True, description="Return only active categories"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List category rows from book_categories table."""
    service = DigitalBookService(db)
    data = await service.list_categories(active_only=active_only)
    return success_response(data=data, message="Digital book categories retrieved successfully")


@router.post(
    "/categories",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create or update category metadata",
    description="Upsert category metadata by category_id in book_categories table.",
)
async def create_or_update_digital_book_category(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create or update one category row."""
    content_type = (request.headers.get("content-type") or "").lower()

    def _parse_bool(raw: str | bool | None, default: bool) -> bool:
        if raw is None:
            return default
        if isinstance(raw, bool):
            return raw
        value = str(raw).strip().lower()
        if value in {"1", "true", "yes", "on"}:
            return True
        if value in {"0", "false", "no", "off"}:
            return False
        return default

    payload: BookCategoryCreateRequest
    category_image: UploadFile | None = None

    if "multipart/form-data" in content_type:
        form = await request.form()
        raw_tags = form.get("tags")
        parsed_tags: list[str] | None = None
        if raw_tags is not None:
            parsed_tags = [item.strip() for item in str(raw_tags).split(",") if item and item.strip()]

        category_image_candidate = form.get("category_image")
        category_image = (
            category_image_candidate
            if category_image_candidate is not None and hasattr(category_image_candidate, "filename")
            else None
        )
        category_id_raw = form.get("category_id")
        payload = BookCategoryCreateRequest(
            category_id=int(str(category_id_raw)) if category_id_raw not in (None, "") else None,
            name=str(form.get("name") or "").strip(),
            tags=parsed_tags,
            label=(str(form.get("label")).strip() if form.get("label") not in (None, "") else None),
            description=(str(form.get("description")).strip() if form.get("description") not in (None, "") else None),
            category_image_url=(str(form.get("category_image_url")).strip() if form.get("category_image_url") not in (None, "") else None),
            emoji=(str(form.get("emoji")).strip() if form.get("emoji") not in (None, "") else None),
            color=(str(form.get("color")).strip() if form.get("color") not in (None, "") else None),
            grad=(str(form.get("grad")).strip() if form.get("grad") not in (None, "") else None),
            personalized=_parse_bool(form.get("personalized"), False),
            is_active=_parse_bool(form.get("is_active"), True),
            category_type=(str(form.get("category_type")).strip() if form.get("category_type") not in (None, "") else None),
        )
    else:
        payload = BookCategoryCreateRequest.model_validate(await request.json())

    service = DigitalBookService(db)
    data = await service.create_or_update_category(payload, category_image=category_image)
    return success_response(data=data, message="Digital book category saved successfully")


@router.delete(
    "/categories/{category_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Delete a book category",
    description="Delete a book_categories row by category_id.",
)
async def delete_digital_book_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Delete one category by category_id."""
    service = DigitalBookService(db)
    data = await service.delete_category(category_id)
    return success_response(data=data, message="Digital book category deleted successfully")


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
    "/attribute-options",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get configurable book attribute options",
    description="Return admin-managed option lists for book_type, theme, language, and genre.",
)
async def get_digital_book_attribute_options(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    service = DigitalBookService(db)
    data = await service.list_attribute_options()
    return success_response(data=data, message="Digital book attribute options retrieved successfully")


@router.post(
    "/attribute-options",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create configurable book attribute option",
    description="Create an option for one of: book_type, theme, language, genre.",
)
async def create_digital_book_attribute_option(
    payload: BookAttributeOptionCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = DigitalBookService(db)
    data = await service.create_attribute_option(payload.option_type, payload.value)
    return success_response(data=data, message="Digital book attribute option saved successfully")


@router.delete(
    "/attribute-options/{option_type}/{value}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Delete configurable book attribute option",
    description="Delete an option for one of: book_type, theme, language, genre.",
)
async def delete_digital_book_attribute_option(
    option_type: str,
    value: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = DigitalBookService(db)
    data = await service.delete_attribute_option(option_type, value)
    return success_response(data=data, message="Digital book attribute option deleted successfully")


@router.get(
    "/category/{category_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get digital books by category",
    description="Return digital books belonging to a specific category (path param). Supports all the same optional filters as the main list endpoint.",
)
async def get_digital_books_by_collection(
    category_id: int,
    search: str | None = Query(None, max_length=120),
    book_type: str | None = Query(None, max_length=50),
    genre: str | None = Query(None, max_length=100),
    is_bestseller: bool | None = Query(None),
    language: str | None = Query(None, max_length=50),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    limit: int = Query(60, ge=1, le=120),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get digital books filtered by category_id (path param)."""
    service = DigitalBookService(db)
    data = await service.list_books(
        search=search,
        book_type=book_type,
        genre=genre,
        category_id=category_id,
        is_bestseller=is_bestseller,
        language=language,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
        offset=offset,
    )
    return success_response(data=data, message="Digital books retrieved successfully")


@router.get(
    "/{book_id:int}",
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


@router.patch(
    "/{book_id:int}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Update digital book",
    description="Partially update digital book metadata (category, bestseller tag, price, etc.). File assets are not changed here.",
)
async def update_digital_book(
    book_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update digital book metadata and optionally replace uploaded files."""
    service = DigitalBookService(db)

    def _to_opt_str(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _to_opt_int(value: Any) -> int | None:
        text = _to_opt_str(value)
        return int(text) if text is not None else None

    def _to_opt_float(value: Any) -> float | None:
        text = _to_opt_str(value)
        return float(text) if text is not None else None

    def _to_opt_bool(value: Any) -> bool | None:
        text = _to_opt_str(value)
        if text is None:
            return None
        lowered = text.lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
        return None

    content_type = (request.headers.get("content-type") or "").lower()
    if "multipart/form-data" in content_type:
        form = await request.form()
        payload = DigitalBookUpdateRequest(
            book_name=_to_opt_str(form.get("book_name")),
            description=_to_opt_str(form.get("description")),
            category_id=_to_opt_int(form.get("category_id")),
            emoji=_to_opt_str(form.get("emoji")),
            age_group=_to_opt_str(form.get("age_group")),
            total_pages=_to_opt_int(form.get("total_pages")),
            book_type=_to_opt_str(form.get("book_type")),
            style=_to_opt_str(form.get("style")),
            language=_to_opt_str(form.get("language")),
            genre=_to_opt_str(form.get("genre")),
            price=_to_opt_float(form.get("price")),
            rating=_to_opt_float(form.get("rating")),
            total_ratings=_to_opt_int(form.get("total_ratings")),
            download_count=_to_opt_int(form.get("download_count")),
            is_bestseller=_to_opt_bool(form.get("is_bestseller")),
            is_personalized=_to_opt_bool(form.get("is_personalized")),
        )

        def _file(name: str) -> UploadFile | None:
            candidate = form.get(name)
            if candidate is None or not hasattr(candidate, "filename"):
                return None
            return candidate if getattr(candidate, "filename", "") else None

        data = await service.update_book_with_files(
            book_id,
            payload,
            cover_image=_file("cover_image"),
            front_image=_file("front_image"),
            back_image=_file("back_image"),
            page_1_image=_file("page_1_image"),
            page_2_image=_file("page_2_image"),
            page_3_image=_file("page_3_image"),
            page_4_image=_file("page_4_image"),
            book_file=_file("book_file"),
        )
    else:
        payload = DigitalBookUpdateRequest.model_validate(await request.json())
        data = await service.update_book(book_id, payload)

    return success_response(data=data, message="Digital book updated successfully")


@router.delete(
    "/{book_id:int}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Delete a digital book",
    description="Delete a digital book record by ID. R2 assets (images/PDF) are not removed.",
)
async def delete_digital_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Delete one digital book by ID."""
    service = DigitalBookService(db)
    data = await service.delete_book(book_id)
    return success_response(data=data, message="Digital book deleted successfully")


@router.post(
    "/{book_id:int}/category/{category_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Add/Set book category",
    description="Assign a category to an existing digital book. Pass the numeric category_id as a path param (e.g. 1).",
)
async def add_digital_book_category(
    book_id: int,
    category_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Set or update category for a book."""
    service = DigitalBookService(db)
    data = await service.add_book_category(book_id=book_id, category_id=category_id)
    return success_response(data=data, message="Digital book category added successfully")


@router.get(
    "/{book_id:int}/preview-pdf",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get watermarked preview PDF URL",
    description="Generate a temporary watermarked PDF preview URL for a digital book.",
)
async def get_digital_book_preview_pdf(book_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Create a watermarked preview and return a presigned URL."""
    service = DigitalBookService(db)
    data = await service.get_watermarked_preview(book_id)
    return success_response(data=data, message="Digital book preview generated successfully")


@router.get(
    "/images/{object_path:path}",
    status_code=200,
    summary="Proxy an image from storage",
    description="Stream a stored image (category or book cover) through the API. No auth required.",
    include_in_schema=False,
)
async def serve_storage_image(object_path: str) -> Response:
    """Proxy storage images so the browser can always reach them."""
    storage = StorageService()
    try:
        data = await storage.download_file(object_path)
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Image not found")
    except Exception:
        raise HTTPException(status_code=502, detail="Could not load image from storage")

    content_type = mimetypes.guess_type(object_path)[0] or "image/jpeg"
    return Response(
        content=data,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=3600"},
    )

