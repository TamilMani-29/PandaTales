"""Payment API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import success_response
from app.common.exceptions import BadRequestException, ForbiddenException
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.digital_book import (
    DigitalBookPaymentCreateRequest,
    DigitalBookPaymentVerifyRequest,
    DigitalBookPurchaseRequest,
)
from app.services.digital_book import DigitalBookService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/digital-books/create-order",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create digital payment order",
    description="Collect delivery contact (email/whatsapp), create Razorpay order, and persist pending payment record.",
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
    description="Verify Razorpay signature, mark payment status, and email PDF if delivery is email.",
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
