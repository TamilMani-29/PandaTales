"""Razorpay Payment Service"""

import hashlib
import hmac
from datetime import datetime, timezone
from uuid import UUID

import razorpay

from app.common import get_logger
from app.common.exceptions import BadRequestException, NotFoundException
from app.core.config import get_settings
from app.models.order import Order
from app.repositories.order import OrderRepository
from app.repositories.generated_book import GeneratedBookRepository
from app.schemas.order import CreateOrderRequest, CreateOrderResponse, OrderResponse

logger = get_logger(__name__)

# Prices in paise (1 INR = 100 paise)
FORMAT_PRICES: dict[str, int] = {
    "digital": 49900,      # ₹499
    "softcover": 129900,   # ₹1,299
    "hardcover": 179900,   # ₹1,799
}


class PaymentService:
    def __init__(self, db) -> None:
        self.db = db
        self.order_repo = OrderRepository(db)
        self.book_repo = GeneratedBookRepository(db)
        settings = get_settings()
        self._key_id = settings.RAZORPAY_KEY_ID
        self._key_secret = settings.RAZORPAY_KEY_SECRET
        # Only initialise the client when credentials are present
        self._client = (
            razorpay.Client(auth=(self._key_id, self._key_secret))
            if self._key_id and self._key_secret
            else None
        )

    async def create_order(
        self, user_id: UUID, data: CreateOrderRequest
    ) -> CreateOrderResponse:
        """Create a Razorpay order and persist it."""
        if not self._client:
            raise BadRequestException(
                "Payment gateway is not configured. "
                "Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in the environment."
            )

        # Validate book belongs to this user
        book = await self.book_repo.get_by_id(data.book_id, user_id)
        if not book:
            raise NotFoundException("Book not found")

        amount = FORMAT_PRICES.get(data.format)
        if amount is None:
            raise BadRequestException(f"Invalid format: {data.format}")

        # Create Razorpay order
        rz_order = self._client.order.create(
            {
                "amount": amount,
                "currency": "INR",
                "payment_capture": 1,  # auto-capture
                "notes": {
                    "book_id": str(data.book_id),
                    "user_id": str(user_id),
                    "format": data.format,
                },
            }
        )
        logger.info(
            "razorpay_order_created",
            rz_order_id=rz_order["id"],
            user_id=str(user_id),
            book_id=str(data.book_id),
        )

        # Persist our order record
        order = Order(
            user_id=user_id,
            book_id=data.book_id,
            format=data.format,
            amount=amount,
            currency="INR",
            razorpay_order_id=rz_order["id"],
            status="created",
        )
        order = await self.order_repo.create(order)
        await self.db.commit()

        return CreateOrderResponse(
            order_id=order.id,
            razorpay_order_id=rz_order["id"],
            amount=amount,
            currency="INR",
            key_id=self._key_id,
        )

    async def verify_payment(
        self,
        user_id: UUID,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> OrderResponse:
        """
        Verify the HMAC-SHA256 signature from Razorpay and mark the order paid.
        Signature = HMAC-SHA256(key_secret, razorpay_order_id + '|' + razorpay_payment_id)
        """
        order = await self.order_repo.get_by_razorpay_order_id(razorpay_order_id)
        if not order or order.user_id != user_id:
            raise NotFoundException("Order not found")

        if order.status == "paid":
            # Idempotent: already processed
            return OrderResponse.model_validate(order)

        # HMAC verification
        expected = hmac.new(
            self._key_secret.encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, razorpay_signature):
            logger.warning(
                "razorpay_signature_mismatch",
                rz_order_id=razorpay_order_id,
                user_id=str(user_id),
            )
            raise BadRequestException("Payment verification failed: invalid signature")

        # Mark as paid
        order.razorpay_payment_id = razorpay_payment_id
        order.razorpay_signature = razorpay_signature
        order.status = "paid"
        order.paid_at = datetime.now(timezone.utc)

        # If digital purchase, mark the book as purchased
        if order.format == "digital":
            book = await self.book_repo.get_by_id(order.book_id)
            if book:
                book.is_purchased = True
                book.purchased_at = datetime.now(timezone.utc)

        await self.order_repo.save(order)
        await self.db.commit()

        logger.info(
            "payment_verified",
            rz_order_id=razorpay_order_id,
            rz_payment_id=razorpay_payment_id,
            user_id=str(user_id),
        )
        return OrderResponse.model_validate(order)

    async def list_orders(self, user_id: UUID) -> list[OrderResponse]:
        orders = await self.order_repo.get_by_user(user_id)
        return [OrderResponse.model_validate(o) for o in orders]
