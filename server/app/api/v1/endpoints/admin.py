"""Admin API routes with fixed credentials for internal panel access."""

from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import BadRequestException, UnauthorizedException, success_response
from app.db.session import get_db
from app.models.digital_book_order import DigitalBookOrder
from app.models.generated_book import GeneratedBook
from app.models.user import User
from app.services.digital_book import DigitalBookService
from app.services.storage import StorageService

router = APIRouter(prefix="/admin", tags=["Admin"])

ADMIN_USERNAME = "admin@123"
ADMIN_PASSWORD = "admin@123"


class AdminLoginRequest(BaseModel):
    """Login payload for admin panel."""

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class AdminPersonalizedOrderStatusUpdateRequest(BaseModel):
    """Admin payload to update payment and/or order status."""

    payment_status: str | None = Field(default=None, min_length=1, max_length=20)
    order_status: str | None = Field(default=None, min_length=1, max_length=20)


def _validate_admin_credentials(username: str, password: str) -> None:
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        raise UnauthorizedException("Invalid admin credentials")


def require_admin_headers(
    x_admin_username: str = Header(..., alias="X-Admin-Username"),
    x_admin_password: str = Header(..., alias="X-Admin-Password"),
) -> None:
    """Protect admin endpoints using fixed header credentials."""
    _validate_admin_credentials(x_admin_username, x_admin_password)


@router.post(
    "/login",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Admin login",
    description="Validate fixed admin username/password for admin panel access.",
)
async def admin_login(payload: AdminLoginRequest) -> dict:
    """Validate static admin credentials."""
    _validate_admin_credentials(payload.username, payload.password)
    return success_response(
        data={
            "authenticated": True,
            "username": payload.username,
        },
        message="Admin login successful",
    )


@router.get(
    "/users",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List users with payment summary",
    description="Return all users with payment count, total spend, and last payment timestamp.",
)
async def admin_list_users(
    _: None = Depends(require_admin_headers),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List users with aggregate payment stats for admin UI."""
    query = (
        select(
            User.id,
            User.full_name,
            User.email,
            User.role,
            func.count(DigitalBookOrder.id).label("payment_count"),
            func.coalesce(func.sum(DigitalBookOrder.amount), 0).label("total_spend"),
            func.max(DigitalBookOrder.created_at).label("last_payment_at"),
        )
        .outerjoin(DigitalBookOrder, DigitalBookOrder.user_id == User.id)
        .group_by(User.id)
        .order_by(User.created_at.desc())
    )

    rows = (await db.execute(query)).all()
    items = [
        {
            "id": str(row.id),
            "full_name": row.full_name,
            "email": row.email,
            "role": row.role,
            "payment_count": int(row.payment_count or 0),
            "total_spend": int(row.total_spend or 0),
            "last_payment_at": row.last_payment_at,
        }
        for row in rows
    ]

    return success_response(data=items, message="Admin users retrieved successfully")


@router.get(
    "/users/{user_id}/payments",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get user payment details",
    description="Return digital payment history of a selected user for admin panel.",
)
async def admin_get_user_payments(
    user_id: str,
    _: None = Depends(require_admin_headers),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get selected user's digital payment history."""
    try:
        target_user_id = UUID(user_id)
    except ValueError as exc:
        raise BadRequestException("Invalid user ID format") from exc

    service = DigitalBookService(db)
    history = await service.list_payment_history(user_id=target_user_id)
    return success_response(data=history, message="User payment details retrieved successfully")


@router.get(
    "/personalized-orders",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List personalized orders",
    description="Return all personalized book submissions with uploaded photos, child/parent details, payment status and order status.",
)
async def admin_list_personalized_orders(
    limit: int = 100,
    _: None = Depends(require_admin_headers),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List personalized orders by querying GeneratedBook directly."""
    safe_limit = max(1, min(limit, 300))

    query = (
        select(GeneratedBook)
        .where(GeneratedBook.generation_type == "photo_to_coloring")
        .order_by(GeneratedBook.created_at.desc())
        .limit(safe_limit)
    )
    rows = (await db.execute(query)).scalars().all()

    storage = StorageService()
    items: list[dict] = []
    for book in rows:
        photos: list[dict] = []
        for object_name in (book.photos or []):
            photo_url: str | None = None
            try:
                photo_url = await storage.get_file_url(
                    object_name,
                    expires=timedelta(hours=1),
                    check_exists=False,
                )
            except Exception:
                photo_url = None
            photos.append({
                "object_name": object_name,
                "url": photo_url,
            })

        items.append(
            {
                "book_id": str(book.id),
                "created_at": book.created_at,
                "child_name": book.child_name,
                "child_age": book.child_age,
                "child_gender": book.child_gender,
                "parent_email": book.parent_email,
                "whatsapp_number": book.whatsapp_number,
                "payment_status": book.payment_status,
                "order_status": book.status,
                "generation_type": book.generation_type,
                "selected_theme_name": book.selected_theme_name,
                "is_purchased": bool(book.is_purchased),
                "purchased_at": book.purchased_at,
                "photos": photos,
                "user_id": str(book.user_id),
            }
        )

    return success_response(data=items, message="Personalized orders retrieved successfully")


@router.patch(
    "/personalized-orders/{book_id}/status",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Update personalized order statuses",
    description="Update payment_status and/or order status for a personalized book submission.",
)
async def admin_update_personalized_order_status(
    book_id: str,
    payload: AdminPersonalizedOrderStatusUpdateRequest,
    _: None = Depends(require_admin_headers),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update payment and/or order status directly on GeneratedBook."""
    try:
        target_book_id = UUID(book_id)
    except ValueError as exc:
        raise BadRequestException("Invalid book ID format") from exc

    if payload.payment_status is None and payload.order_status is None:
        raise BadRequestException("Provide at least one field: payment_status or order_status")

    book = await db.get(GeneratedBook, target_book_id)
    if not book:
        raise BadRequestException("Personalized order not found")

    allowed_payment_statuses = {"pending", "paid", "failed"}
    allowed_order_statuses = {"queued", "processing", "completed", "failed", "cancelled"}

    if payload.payment_status is not None:
        new_payment_status = payload.payment_status.strip().lower()
        if new_payment_status not in allowed_payment_statuses:
            raise BadRequestException(
                "Invalid payment_status. Allowed: pending, paid, failed"
            )
        book.payment_status = new_payment_status

    if payload.order_status is not None:
        new_order_status = payload.order_status.strip().lower()
        if new_order_status not in allowed_order_statuses:
            raise BadRequestException(
                "Invalid order_status. Allowed: queued, processing, completed, failed, cancelled"
            )
        book.status = new_order_status

    await db.commit()
    await db.refresh(book)

    return success_response(
        data={
            "book_id": str(book.id),
            "payment_status": book.payment_status,
            "order_status": book.status,
        },
        message="Personalized order status updated successfully",
    )
