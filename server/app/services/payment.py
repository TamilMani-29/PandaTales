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
from sqlalchemy import and_, func, or_, select

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
# - Digital purchases: 5%
# - Physical books (softcover/hardcover): 0%
GST_RATES_BY_FORMAT: dict[str, int] = {
    "digital": 5,
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

        user_result = await self.db.execute(select(User).where(User.id == order.user_id))
        user = user_result.scalar_one_or_none()
        invoice_number = await self._build_checkout_invoice_number(order)

        # Send tax invoice via Razorpay when gateway credentials are present.
        if user and user.email:
            try:
                await self._create_and_notify_razorpay_invoice(
                    order=order,
                    user=user,
                    invoice_number=invoice_number,
                )
            except Exception as exc:
                logger.warning(
                    "razorpay_checkout_invoice_failed",
                    order_id=str(order.id),
                    user_id=str(user_id),
                    error=str(exc),
                )

        # Send custom invoice email with PDF attachment.
        try:
            await self._send_order_invoice_email(
                order,
                user=user,
                invoice_number=invoice_number,
            )
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

    async def _send_order_invoice_email(
        self,
        order: Order,
        user: User | None = None,
        invoice_number: str | None = None,
    ) -> None:
        settings = get_settings()
        if not settings.SMTP_HOST or not settings.SMTP_PORT:
            raise BadRequestException("SMTP is not configured")
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            raise BadRequestException("SMTP credentials are missing")

        if user is None:
            user_result = await self.db.execute(select(User).where(User.id == order.user_id))
            user = user_result.scalar_one_or_none()
        if not user or not user.email:
            return

        gst_rate_percent = GST_RATES_BY_FORMAT.get(order.format, 0)
        taxable_amount = self._derive_taxable_from_total(order.amount, gst_rate_percent)
        gst_amount = max(order.amount - taxable_amount, 0)
        if not invoice_number:
            invoice_number = await self._build_checkout_invoice_number(order)

        hsn_sac_code = self._hsn_sac_for_format(order.format)
        is_intra_state = self._is_intra_state_supply()
        igst_amount, cgst_amount, sgst_amount = self._split_gst_components(
            gst_amount,
            is_intra_state=is_intra_state,
        )
        phone = (user.phone or "").strip()

        invoice_pdf = self._build_invoice_pdf_bytes(
            invoice_number=invoice_number,
            order=order,
            customer_name=user.full_name or user.first_name,
            customer_email=user.email,
            customer_phone=phone,
            taxable_amount_paise=taxable_amount,
            gst_rate_percent=gst_rate_percent,
            gst_amount_paise=gst_amount,
            igst_amount_paise=igst_amount,
            cgst_amount_paise=cgst_amount,
            sgst_amount_paise=sgst_amount,
            hsn_sac_code=hsn_sac_code,
            total_amount_paise=order.amount,
        )

        message = EmailMessage()
        message["Subject"] = f"Invoice for order #{order.id} - Panda Tales"
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = user.email
        message.set_content(
            f"Hi {user.full_name or user.first_name or 'Customer'},\n\n"
            "Thanks for your order with Panda Tales.\n"
            "Please find your GST invoice attached.\n\n"
            f"Invoice Number: {invoice_number}\n"
            f"Customer Name: {user.full_name or user.first_name or 'Customer'}\n"
            f"Customer Email: {user.email}\n"
            f"Customer Phone: {phone or 'Unavailable'}\n"
            f"HSN/SAC: {hsn_sac_code}\n"
            f"Taxable Amount: INR {taxable_amount / 100:.2f}\n"
            f"GST ({gst_rate_percent}%): INR {gst_amount / 100:.2f}\n"
            f"IGST: INR {igst_amount / 100:.2f}\n"
            f"CGST: INR {cgst_amount / 100:.2f}\n"
            f"SGST: INR {sgst_amount / 100:.2f}\n"
            f"Grand Total: INR {order.amount / 100:.2f}\n\n"
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

    async def _create_and_notify_razorpay_invoice(
        self,
        *,
        order: Order,
        user: User,
        invoice_number: str,
    ) -> None:
        if not self._client:
            return

        gst_rate_percent = GST_RATES_BY_FORMAT.get(order.format, 0)
        taxable_amount = self._derive_taxable_from_total(order.amount, gst_rate_percent)
        gst_amount = max(order.amount - taxable_amount, 0)
        hsn_sac_code = self._hsn_sac_for_format(order.format)
        is_intra_state = self._is_intra_state_supply()
        igst_amount, cgst_amount, sgst_amount = self._split_gst_components(
            gst_amount,
            is_intra_state=is_intra_state,
        )

        customer_contact = self._normalize_contact_number(user.phone)
        invoice_payload: dict = {
            "type": "invoice",
            "draft": 0,
            "currency": "INR",
            "receipt": invoice_number,
            "description": f"Checkout order #{order.id}",
            "customer": {
                "name": (user.full_name or user.first_name or "Customer").strip() or "Customer",
                "email": user.email,
                "contact": customer_contact,
            },
            "line_items": [
                {
                    "name": f"{order.format.title()} book purchase",
                    "description": "Taxable amount",
                    "amount": taxable_amount,
                    "currency": "INR",
                    "quantity": 1,
                    "hsn_code": hsn_sac_code,
                },
                {
                    "name": f"GST @{gst_rate_percent}%",
                    "description": "GST component",
                    "amount": gst_amount,
                    "currency": "INR",
                    "quantity": 1,
                    "hsn_code": hsn_sac_code,
                },
            ],
            "email_notify": 1,
            "sms_notify": 0,
            "notes": {
                "order_id": str(order.id),
                "payment_id": order.razorpay_payment_id or "",
                "seller_gstin": get_settings().SELLER_GSTIN,
                "customer_name": user.full_name or user.first_name or "Customer",
                "customer_email": user.email,
                "customer_phone": user.phone or "",
                "hsn_sac": hsn_sac_code,
                "taxable_amount_inr": f"{taxable_amount / 100:.2f}",
                "gst_rate_percent": str(gst_rate_percent),
                "gst_amount_inr": f"{gst_amount / 100:.2f}",
                "igst_inr": f"{igst_amount / 100:.2f}",
                "cgst_inr": f"{cgst_amount / 100:.2f}",
                "sgst_inr": f"{sgst_amount / 100:.2f}",
                "total_amount_inr": f"{order.amount / 100:.2f}",
            },
        }

        if not customer_contact:
            invoice_payload["customer"].pop("contact", None)

        rz_invoice = await asyncio.to_thread(self._client.invoice.create, invoice_payload)
        invoice_id = rz_invoice.get("id")
        if invoice_id:
            await asyncio.to_thread(self._client.invoice.notify_by, invoice_id, "email")

    @staticmethod
    def _normalize_contact_number(phone: str | None) -> str:
        if not phone:
            return ""
        digits = "".join(ch for ch in str(phone) if ch.isdigit())
        if len(digits) < 10:
            return ""
        return digits[-15:]

    @staticmethod
    def _split_gst_components(gst_amount_paise: int, *, is_intra_state: bool) -> tuple[int, int, int]:
        if gst_amount_paise <= 0:
            return 0, 0, 0
        if not is_intra_state:
            return gst_amount_paise, 0, 0
        cgst = gst_amount_paise // 2
        sgst = gst_amount_paise - cgst
        return 0, cgst, sgst

    @staticmethod
    def _hsn_sac_for_format(order_format: str) -> str:
        if order_format == "digital":
            return "99843"
        return "4901"

    @staticmethod
    def _is_intra_state_supply() -> bool:
        return bool(get_settings().GST_INTRA_STATE_BY_DEFAULT)

    async def _build_checkout_invoice_number(self, order: Order) -> str:
        paid_at = order.paid_at or datetime.now(timezone.utc)
        invoice_date = paid_at.date()

        seq_query = select(func.count(Order.id)).where(
            Order.paid_at.is_not(None),
            func.date(Order.paid_at) == invoice_date,
            or_(
                Order.paid_at < paid_at,
                and_(Order.paid_at == paid_at, Order.id <= order.id),
            ),
        )
        sequence = (await self.db.scalar(seq_query)) or 1
        return f"INV-{invoice_date:%Y}-{int(sequence):06d}"

    def _build_invoice_pdf_bytes(
        self,
        *,
        invoice_number: str,
        order: Order,
        customer_name: str,
        customer_email: str,
        customer_phone: str,
        taxable_amount_paise: int,
        gst_rate_percent: int,
        gst_amount_paise: int,
        igst_amount_paise: int,
        cgst_amount_paise: int,
        sgst_amount_paise: int,
        hsn_sac_code: str,
        total_amount_paise: int,
    ) -> bytes:
        settings = get_settings()
        buffer = io.BytesIO()
        page_w, page_h = A4
        pdf = canvas.Canvas(buffer, pagesize=A4)

        left = 50
        right = page_w - 50
        y = page_h - 50

        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(left, y, "TAX INVOICE")
        pdf.setFont("Helvetica", 9)
        pdf.drawString(left, y - 14, "Panda Tales")

        meta_x = right - 230
        meta_top = y + 8
        meta_bottom = y - 72
        pdf.rect(meta_x, meta_bottom, 230, meta_top - meta_bottom)
        pdf.setFont("Helvetica", 9)
        pdf.drawString(meta_x + 10, meta_top - 14, f"Invoice No: {invoice_number}")
        pdf.drawString(meta_x + 10, meta_top - 28, f"Invoice Date: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}")
        pdf.drawString(meta_x + 10, meta_top - 42, f"Order ID: {order.id}")
        if order.razorpay_payment_id:
            pdf.drawString(meta_x + 10, meta_top - 56, f"Payment ID: {order.razorpay_payment_id}")
        elif order.paid_at:
            pdf.drawString(meta_x + 10, meta_top - 56, f"Paid At: {order.paid_at:%Y-%m-%d %H:%M UTC}")

        y = meta_bottom - 16
        box_h = 68
        gap = 12
        half_w = (right - left - gap) / 2

        pdf.rect(left, y - box_h, half_w, box_h)
        pdf.rect(left + half_w + gap, y - box_h, half_w, box_h)

        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(left + 8, y - 14, "Bill To")
        pdf.drawString(left + half_w + gap + 8, y - 14, "Seller")

        pdf.setFont("Helvetica", 9)
        pdf.drawString(left + 8, y - 30, customer_name or "Customer")
        pdf.drawString(left + 8, y - 44, customer_email)
        pdf.drawString(left + 8, y - 58, customer_phone or "Unavailable")

        pdf.drawString(left + half_w + gap + 8, y - 30, settings.SMTP_FROM_NAME)
        pdf.drawString(left + half_w + gap + 8, y - 44, f"GSTIN: {settings.SELLER_GSTIN}")
        pdf.drawString(left + half_w + gap + 8, y - 58, "Country: India")

        y -= box_h + 20

        table_top = y
        row_h = 20
        table_rows = 2
        table_h = row_h * table_rows
        col_widths = [26, 184, 66, 80, 44, 70, 76]
        table_w = sum(col_widths)

        pdf.rect(left, table_top - table_h, table_w, table_h)

        x = left
        for w in col_widths[:-1]:
            x += w
            pdf.line(x, table_top, x, table_top - table_h)

        pdf.line(left, table_top - row_h, left + table_w, table_top - row_h)

        pdf.setFillColorRGB(0.95, 0.95, 0.95)
        pdf.rect(left, table_top - row_h, table_w, row_h, fill=1, stroke=0)
        pdf.setFillColorRGB(0, 0, 0)

        headers = ["#", "Description", "HSN/SAC", "Taxable", "GST %", "GST Amt", "Total"]
        x = left
        pdf.setFont("Helvetica-Bold", 9)
        for idx, title in enumerate(headers):
            align_right = idx in (3, 5, 6)
            if align_right:
                pdf.drawRightString(x + col_widths[idx] - 4, table_top - 14, title)
            else:
                pdf.drawString(x + 4, table_top - 14, title)
            x += col_widths[idx]

        item_name = f"{order.format.title()} book purchase"
        values = [
            "1",
            item_name,
            hsn_sac_code,
            f"INR {taxable_amount_paise / 100:.2f}",
            f"{gst_rate_percent}%",
            f"INR {gst_amount_paise / 100:.2f}",
            f"INR {total_amount_paise / 100:.2f}",
        ]

        x = left
        pdf.setFont("Helvetica", 9)
        for idx, value in enumerate(values):
            align_right = idx in (3, 5, 6)
            if align_right:
                pdf.drawRightString(x + col_widths[idx] - 4, table_top - row_h - 14, value)
            else:
                pdf.drawString(x + 4, table_top - row_h - 14, value)
            x += col_widths[idx]

        y = table_top - table_h - 16

        summary_w = 230
        summary_h = 92
        summary_x = right - summary_w
        pdf.rect(summary_x, y - summary_h, summary_w, summary_h)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(summary_x + 8, y - 14, "Tax Summary")
        pdf.setFont("Helvetica", 9)
        pdf.drawString(summary_x + 8, y - 30, f"IGST: INR {igst_amount_paise / 100:.2f}")
        pdf.drawString(summary_x + 8, y - 44, f"CGST: INR {cgst_amount_paise / 100:.2f}")
        pdf.drawString(summary_x + 8, y - 58, f"SGST: INR {sgst_amount_paise / 100:.2f}")
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(summary_x + 8, y - 78, "Grand Total")
        pdf.drawRightString(summary_x + summary_w - 8, y - 78, f"INR {total_amount_paise / 100:.2f}")

        pdf.setFont("Helvetica", 8)
        pdf.drawString(left, y - summary_h - 14, "GST summary: Digital products 5%, physical books 0% (exempt).")

        pdf.showPage()
        pdf.save()
        return buffer.getvalue()
