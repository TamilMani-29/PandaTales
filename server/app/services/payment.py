"""Razorpay Payment Service"""

import asyncio
import hashlib
import hmac
import io
import smtplib
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from email.message import EmailMessage
from uuid import UUID

import razorpay
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import select

from app.common import get_logger
from app.common.exceptions import BadRequestException, NotFoundException
from app.core.config import get_settings
from app.models.order import Order
from app.models.user import User
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

# GST rates by format
# - Digital purchases: 18%
# - Physical books (softcover/hardcover): 0%
GST_RATES_BY_FORMAT: dict[str, int] = {
    "digital": 18,
    "softcover": 0,
    "hardcover": 0,
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

        gst_rate_percent = GST_RATES_BY_FORMAT.get(data.format, 0)
        gst_amount = self._calculate_gst_amount_paise(amount, gst_rate_percent)
        total_amount = amount + gst_amount

        # Create Razorpay order
        rz_order = self._client.order.create(
            {
                "amount": total_amount,
                "currency": "INR",
                "payment_capture": 1,  # auto-capture
                "notes": {
                    "book_id": str(data.book_id),
                    "user_id": str(user_id),
                    "format": data.format,
                    "taxable_amount": str(amount),
                    "gst_rate_percent": str(gst_rate_percent),
                    "gst_amount": str(gst_amount),
                    "total_amount": str(total_amount),
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
            amount=total_amount,
            currency="INR",
            razorpay_order_id=rz_order["id"],
            status="created",
            whatsapp_number=data.whatsapp_number,
        )
        order = await self.order_repo.create(order)
        await self.db.commit()

        return CreateOrderResponse(
            order_id=order.id,
            razorpay_order_id=rz_order["id"],
            amount=total_amount,
            taxable_amount=amount,
            gst_rate_percent=gst_rate_percent,
            gst_amount=gst_amount,
            total_amount=total_amount,
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

        # Send invoice to purchaser email (non-blocking in payment confirmation path)
        try:
            await self._send_order_invoice_email(order)
        except Exception as exc:
            logger.warning(
                "checkout_invoice_email_failed",
                order_id=str(order.id),
                user_id=str(user_id),
                error=str(exc),
            )

        await self.order_repo.save(order)
        await self.db.commit()

        logger.info(
            "payment_verified",
            rz_order_id=razorpay_order_id,
            rz_payment_id=razorpay_payment_id,
            user_id=str(user_id),
        )
        return self._to_order_response(order)

    async def list_orders(self, user_id: UUID) -> list[OrderResponse]:
        orders = await self.order_repo.get_by_user(user_id)
        return [self._to_order_response(o) for o in orders]

    @staticmethod
    def _calculate_gst_amount_paise(taxable_amount_paise: int, gst_rate_percent: int) -> int:
        if gst_rate_percent <= 0:
            return 0
        return int(
            (Decimal(taxable_amount_paise) * Decimal(gst_rate_percent) / Decimal("100")).quantize(
                Decimal("1"),
                rounding=ROUND_HALF_UP,
            )
        )

    @staticmethod
    def _derive_taxable_from_total(total_amount_paise: int, gst_rate_percent: int) -> int:
        if gst_rate_percent <= 0:
            return total_amount_paise
        multiplier = Decimal("1") + (Decimal(gst_rate_percent) / Decimal("100"))
        return int((Decimal(total_amount_paise) / multiplier).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    def _to_order_response(self, order: Order) -> OrderResponse:
        gst_rate_percent = GST_RATES_BY_FORMAT.get(order.format, 0)
        taxable_amount = self._derive_taxable_from_total(order.amount, gst_rate_percent)
        gst_amount = max(order.amount - taxable_amount, 0)

        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            book_id=order.book_id,
            format=order.format,
            amount=order.amount,
            taxable_amount=taxable_amount,
            gst_rate_percent=gst_rate_percent,
            gst_amount=gst_amount,
            total_amount=order.amount,
            currency=order.currency,
            razorpay_order_id=order.razorpay_order_id,
            razorpay_payment_id=order.razorpay_payment_id,
            status=order.status,
            paid_at=order.paid_at,
            created_at=order.created_at,
            whatsapp_number=order.whatsapp_number,
        )

    async def _send_order_invoice_email(self, order: Order) -> None:
        settings = get_settings()
        if not settings.SMTP_HOST or not settings.SMTP_PORT:
            raise BadRequestException("SMTP is not configured")
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            raise BadRequestException("SMTP credentials are missing")

        user_result = await self.db.execute(select(User).where(User.id == order.user_id))
        user = user_result.scalar_one_or_none()
        if not user or not user.email:
            return

        gst_rate_percent = GST_RATES_BY_FORMAT.get(order.format, 0)
        taxable_amount = self._derive_taxable_from_total(order.amount, gst_rate_percent)
        gst_amount = max(order.amount - taxable_amount, 0)
        invoice_number = f"INV-CHK-{str(order.id)[:8]}-{datetime.now(timezone.utc):%Y%m%d}"

        invoice_pdf = self._build_invoice_pdf_bytes(
            invoice_number=invoice_number,
            order=order,
            customer_name=user.full_name or user.first_name,
            customer_email=user.email,
            taxable_amount_paise=taxable_amount,
            gst_rate_percent=gst_rate_percent,
            gst_amount_paise=gst_amount,
            total_amount_paise=order.amount,
        )

        message = EmailMessage()
        message["Subject"] = f"Invoice for order #{order.id} - Panda Tales"
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = user.email
        message.set_content(
            "Hi,\n\n"
            "Thanks for your order with Panda Tales.\n"
            "Please find your invoice attached.\n"
            "This invoice includes GST details (including 0% GST for exempt physical books).\n\n"
            "Regards,\n"
            "Panda Tales"
        )
        message.add_attachment(
            invoice_pdf,
            maintype="application",
            subtype="pdf",
            filename=f"invoice-{order.id}.pdf",
        )

        await asyncio.to_thread(self._send_email_sync, message)

    def _send_email_sync(self, message: EmailMessage) -> None:
        settings = get_settings()
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(message)
        except smtplib.SMTPAuthenticationError as exc:
            raise BadRequestException("SMTP authentication failed") from exc
        except Exception as exc:
            raise BadRequestException("Failed to send invoice email") from exc

    def _build_invoice_pdf_bytes(
        self,
        *,
        invoice_number: str,
        order: Order,
        customer_name: str,
        customer_email: str,
        taxable_amount_paise: int,
        gst_rate_percent: int,
        gst_amount_paise: int,
        total_amount_paise: int,
    ) -> bytes:
        settings = get_settings()
        buffer = io.BytesIO()
        page_w, page_h = A4
        pdf = canvas.Canvas(buffer, pagesize=A4)

        left = 50
        y = page_h - 50
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(left, y, "TAX INVOICE")

        y -= 24
        pdf.setFont("Helvetica", 10)
        pdf.drawString(left, y, f"Seller: {settings.SMTP_FROM_NAME}")
        y -= 14
        pdf.drawString(left, y, f"Invoice No: {invoice_number}")
        y -= 14
        pdf.drawString(left, y, f"Order ID: {order.id}")
        y -= 14
        pdf.drawString(left, y, f"Invoice Date: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}")
        y -= 14
        if order.paid_at:
            pdf.drawString(left, y, f"Paid At: {order.paid_at:%Y-%m-%d %H:%M UTC}")
            y -= 14
        if order.razorpay_payment_id:
            pdf.drawString(left, y, f"Payment ID: {order.razorpay_payment_id}")
            y -= 14

        y -= 6
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(left, y, "Bill To")
        y -= 16
        pdf.setFont("Helvetica", 10)
        pdf.drawString(left, y, customer_name or "Customer")
        y -= 14
        pdf.drawString(left, y, customer_email)

        y -= 24
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(left, y, "Item")
        pdf.drawString(left + 260, y, "Taxable")
        pdf.drawString(left + 350, y, "GST")
        pdf.drawString(left + 430, y, "Total")
        y -= 10
        pdf.line(left, y, page_w - left, y)

        y -= 18
        pdf.setFont("Helvetica", 10)
        item_name = f"{order.format.title()} book purchase"
        pdf.drawString(left, y, item_name)
        pdf.drawRightString(left + 330, y, f"INR {taxable_amount_paise / 100:.2f}")
        pdf.drawRightString(left + 420, y, f"{gst_rate_percent}%")
        pdf.drawRightString(page_w - left, y, f"INR {total_amount_paise / 100:.2f}")

        y -= 14
        pdf.drawString(left, y, f"GST Amount: INR {gst_amount_paise / 100:.2f}")
        y -= 20
        pdf.line(left, y, page_w - left, y)
        y -= 18
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(left, y, "Grand Total")
        pdf.drawRightString(page_w - left, y, f"INR {total_amount_paise / 100:.2f}")

        y -= 20
        pdf.setFont("Helvetica", 9)
        pdf.drawString(
            left,
            y,
            "GST summary: Digital products 18%, physical books 0% (exempt).",
        )

        pdf.showPage()
        pdf.save()
        return buffer.getvalue()
