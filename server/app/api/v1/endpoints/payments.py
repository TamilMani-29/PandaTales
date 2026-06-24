"""Payment API routes."""

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import Response
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import get_logger, success_response
from app.common.exceptions import BadRequestException, ForbiddenException, NotFoundException, UnauthorizedException
from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.book import Book
from app.models.digital_book_order import DigitalBookOrder
from app.models.user import User
from app.schemas.digital_book import (
    DigitalBookPaymentCreateRequest,
    DigitalBookPaymentVerifyRequest,
    DigitalBookPurchaseRequest,
)
from app.services.digital_book import DigitalBookService
from app.services.storage import StorageService
from app.utils.pdf_storage import maybe_decompress_pdf, to_pdf_download_filename

router = APIRouter(prefix="/payments", tags=["Payments"])
logger = get_logger(__name__)


@router.post(
    "/digital-books/create-order",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create digital payment order",
    description="Create Razorpay order and persist pending payment record for local digital asset delivery.",
)
async def create_digital_book_payment_order(
    payload: DigitalBookPaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Start digital checkout by creating pending payment order."""
    service = DigitalBookService(db)
    data = await service.create_payment_order(user=current_user, payload=payload)
    return success_response(data=data, message="Digital payment order created")


@router.post(
    "/digital-books/verify",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Verify digital payment",
    description="Verify Razorpay signature, return browser download URLs, and email invoice via Razorpay Invoice API.",
)
async def verify_digital_book_payment(
    payload: DigitalBookPaymentVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Complete digital checkout after successful Razorpay payment."""
    service = DigitalBookService(db)
    data = await service.verify_payment(
        user=current_user,
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature,
    )
    return success_response(data=data, message="Digital payment verified")


@router.get(
    "/digital-books/history",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get my digital payment history",
    description="Return payment history for the authenticated user.",
)
async def get_my_digital_payment_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get current user's digital payment history."""
    service = DigitalBookService(db)
    data = await service.list_payment_history(user_id=current_user.id)
    return success_response(data=data, message="Digital payment history retrieved successfully")


@router.get(
    "/digital-books/history/{user_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get payment history by user ID",
    description="Return payment history for a user ID. User can only fetch their own history.",
)
async def get_digital_payment_history_by_user_id(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get digital payment history by user ID with ownership guard."""
    if current_user.role != "admin" and str(current_user.id) != user_id:
        raise ForbiddenException("You can only access your own payment history")

    try:
        target_user_id = UUID(user_id)
    except ValueError as exc:
        raise BadRequestException("Invalid user ID format") from exc

    service = DigitalBookService(db)
    data = await service.list_payment_history(user_id=target_user_id)
    return success_response(data=data, message="Digital payment history retrieved successfully")


@router.post(
    "/digital-books/purchase",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Purchase digital book",
    description="Backward-compatible endpoint. Creates payment order and returns Razorpay checkout details.",
)
async def purchase_digital_book(
    payload: DigitalBookPurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Record digital purchase and trigger delivery where applicable."""
    service = DigitalBookService(db)
    data = await service.create_purchase_order(user=current_user, payload=payload)
    return success_response(data=data, message="Digital book purchased successfully")


_SUPPORTED_FILE_TYPES = {"book", "cover"}

_DOWNLOAD_TOKEN_TYPE = "digital_order_download"
_DOWNLOAD_TOKEN_EXP_MINUTES = 15


def _verify_razorpay_webhook_signature(*, body: bytes, signature: str | None) -> bool:
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        logger.warning("razorpay_webhook_secret_missing")
        return False
    if not signature:
        return False

    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def _reconcile_order_from_webhook(
    *,
    db: AsyncSession,
    event_type: str,
    payment_entity: dict,
) -> bool:
    razorpay_payment_id = str(payment_entity.get("id") or "").strip()
    razorpay_order_id = str(payment_entity.get("order_id") or "").strip()
    payment_error = str(payment_entity.get("error_description") or payment_entity.get("error_reason") or "").strip() or None

    if not razorpay_order_id and not razorpay_payment_id:
        return False

    order = None
    if razorpay_order_id:
        result = await db.execute(
            select(DigitalBookOrder).where(DigitalBookOrder.razorpay_order_id == razorpay_order_id)
        )
        order = result.scalar_one_or_none()

    if order is None and razorpay_payment_id:
        result = await db.execute(
            select(DigitalBookOrder).where(DigitalBookOrder.razorpay_payment_id == razorpay_payment_id)
        )
        order = result.scalar_one_or_none()

    if order is None:
        return False

    if razorpay_payment_id:
        order.razorpay_payment_id = razorpay_payment_id

    if event_type == "payment.captured":
        order.payment_status = "paid"
        order.status = "paid"
        order.payment_error = None
        if order.paid_at is None:
            order.paid_at = datetime.now(timezone.utc)
    elif event_type == "payment.failed":
        if order.payment_status != "paid":
            order.payment_status = "failed"
            order.status = "failed"
            order.payment_error = payment_error or "Payment failed at gateway"
    else:
        return False

    await db.commit()
    return True


@router.post(
    "/razorpay/webhook",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle Razorpay webhooks and reconcile payment status for digital orders."""
    signature = request.headers.get("X-Razorpay-Signature")
    body = await request.body()

    if not _verify_razorpay_webhook_signature(body=body, signature=signature):
        raise UnauthorizedException("Invalid Razorpay webhook signature")

    try:
        payload = json.loads(body.decode("utf-8")) if body else {}
    except json.JSONDecodeError as exc:
        raise BadRequestException("Invalid webhook payload") from exc

    event_type = str(payload.get("event") or "")
    payment_entity = ((payload.get("payload") or {}).get("payment") or {}).get("entity") or {}

    updated = await _reconcile_order_from_webhook(
        db=db,
        event_type=event_type,
        payment_entity=payment_entity,
    )

    logger.info(
        "razorpay_webhook_processed",
        event=event_type,
        updated=updated,
        razorpay_order_id=payment_entity.get("order_id"),
        razorpay_payment_id=payment_entity.get("id"),
    )

    # Always return 200 for validly signed events to avoid repeated retries.
    return {"status": "ok", "updated": updated}


def _create_download_token(*, user_id: str, order_id: int, file_type: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=_DOWNLOAD_TOKEN_EXP_MINUTES)
    payload = {
        "sub": user_id,
        "order_id": order_id,
        "file_type": file_type,
        "type": _DOWNLOAD_TOKEN_TYPE,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _decode_download_token(*, token: str, order_id: int, file_type: str) -> UUID:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        token_type = payload.get("type")
        token_order_id = int(payload.get("order_id"))
        token_file_type = str(payload.get("file_type"))
        user_id = payload.get("sub")
        if (
            token_type != _DOWNLOAD_TOKEN_TYPE
            or token_order_id != order_id
            or token_file_type != file_type
            or not user_id
        ):
            raise UnauthorizedException("Invalid download token")
        return UUID(str(user_id))
    except (JWTError, ValueError, TypeError):
        raise UnauthorizedException("Invalid or expired download token")


async def _resolve_order_file(
    *,
    db: AsyncSession,
    order_id: int,
    file_type: str,
    user_id: UUID,
) -> tuple[str, str, str]:
    if file_type not in _SUPPORTED_FILE_TYPES:
        raise BadRequestException(f"Invalid file_type '{file_type}'. Must be one of: book, cover")

    result = await db.execute(select(DigitalBookOrder).where(DigitalBookOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundException("Order not found")
    if order.user_id != user_id:
        raise ForbiddenException("You can only download your own orders")
    if order.payment_status != "paid":
        raise BadRequestException("Payment not completed for this order")

    book = await db.get(Book, order.book_id)
    if not book:
        raise NotFoundException("Book not found")

    if file_type == "book":
        object_name = book.book_url
        if not object_name:
            raise NotFoundException("Book PDF is not available")
        media_type = "application/pdf"
        filename = to_pdf_download_filename(object_name, fallback=f"book-{order_id}.pdf")
        return object_name, media_type, filename

    object_name = book.cover_image_url or book.front_image_url or book.back_image_url
    if not object_name:
        raise NotFoundException("Cover image is not available")

    filename = Path(object_name).name or f"cover-{order_id}.jpg"
    suffix = Path(filename).suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        media_type = "image/jpeg"
    elif suffix == ".png":
        media_type = "image/png"
    elif suffix == ".webp":
        media_type = "image/webp"
    else:
        media_type = "application/octet-stream"

    return object_name, media_type, filename


@router.get(
    "/digital-books/{order_id}/download/{file_type}",
    status_code=status.HTTP_200_OK,
    summary="Download paid order file",
    description="Stream a purchased file (book PDF or cover image) to the browser. Only the order owner can download.",
)
async def download_digital_order_file(
    order_id: int,
    file_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Serve purchased artifact from object storage."""
    object_name, media_type, filename = await _resolve_order_file(
        db=db,
        order_id=order_id,
        file_type=file_type,
        user_id=current_user.id,
    )
    storage = StorageService()
    file_bytes = await storage.download_file(object_name)
    if file_type == "book":
        file_bytes = maybe_decompress_pdf(file_bytes, object_name=object_name)

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@router.get(
    "/digital-books/{order_id}/download/{file_type}/public",
    status_code=status.HTTP_200_OK,
    summary="Download paid order file (token)",
    description="Stream a purchased file using a short-lived download token.",
)
async def download_digital_order_file_public(
    order_id: int,
    file_type: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Serve one artifact using a short-lived token in query params."""
    user_id = _decode_download_token(token=token, order_id=order_id, file_type=file_type)
    object_name, media_type, filename = await _resolve_order_file(
        db=db,
        order_id=order_id,
        file_type=file_type,
        user_id=user_id,
    )
    storage = StorageService()
    file_bytes = await storage.download_file(object_name)
    if file_type == "book":
        file_bytes = maybe_decompress_pdf(file_bytes, object_name=object_name)

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
