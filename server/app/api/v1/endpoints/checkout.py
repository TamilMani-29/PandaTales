"""Checkout & Payment API Routes"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import get_logger, success_response
from app.db.session import get_db
from app.schemas.order import CreateOrderRequest, VerifyPaymentRequest
from app.services.payment import PaymentService

logger = get_logger(__name__)

router = APIRouter(prefix="/checkout", tags=["Checkout & Payments"])


# TODO: Replace with real JWT auth dependency
def get_current_user_id() -> UUID:
    """Temporary function to get current user ID - replace with actual auth"""
    return UUID("00000000-0000-0000-0000-000000000001")


@router.post(
    "/create-order",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create Razorpay order",
    description=(
        "Creates a Razorpay order for the selected book format. "
        "Returns the Razorpay order ID and amount so the frontend can open the payment modal."
    ),
)
async def create_order(
    data: CreateOrderRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Step 1 of checkout: create the Razorpay order"""
    service = PaymentService(db)
    result = await service.create_order(user_id, data)
    return success_response(
        data=result.model_dump(),
        message="Order created. Complete payment to proceed.",
    )


@router.post(
    "/verify-payment",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Verify Razorpay payment",
    description=(
        "Verifies the HMAC-SHA256 signature returned by Razorpay after payment. "
        "Marks the order as paid and (for digital) unlocks the download."
    ),
)
async def verify_payment(
    data: VerifyPaymentRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Step 2 of checkout: verify payment signature and fulfil the order"""
    service = PaymentService(db)
    result = await service.verify_payment(
        user_id=user_id,
        razorpay_order_id=data.razorpay_order_id,
        razorpay_payment_id=data.razorpay_payment_id,
        razorpay_signature=data.razorpay_signature,
    )
    return success_response(
        data=result.model_dump(),
        message="Payment verified. Your order is confirmed.",
    )


@router.get(
    "/orders",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="List user orders",
    description="Returns all past orders for the authenticated user.",
)
async def list_orders(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Get the authenticated user's order history"""
    service = PaymentService(db)
    orders = await service.list_orders(user_id)
    return success_response(
        data=[o.model_dump() for o in orders],
        message="Orders retrieved successfully.",
    )
