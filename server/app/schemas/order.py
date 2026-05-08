"""Order / Payment Schemas"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ── Request schemas ────────────────────────────────────────────────────────────

class CreateOrderRequest(BaseModel):
    """Create a Razorpay order for a book purchase"""

    book_id: UUID
    format: str = Field(..., pattern="^(digital|softcover|hardcover)$")
    whatsapp_number: str | None = Field(None, max_length=20, description="WhatsApp number for print order updates")


class VerifyPaymentRequest(BaseModel):
    """Verify Razorpay payment after the user completes checkout"""

    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


# ── Response schemas ───────────────────────────────────────────────────────────

class CreateOrderResponse(BaseModel):
    """Returned to the frontend so it can open the Razorpay modal"""

    order_id: UUID                  # our internal Order.id
    razorpay_order_id: str          # e.g. "order_ABC123"
    amount: int                     # in paise
    taxable_amount: int             # base amount before GST (paise)
    gst_rate_percent: int           # GST percentage used for this format
    gst_amount: int                 # GST amount in paise
    total_amount: int               # payable amount in paise
    currency: str                   # "INR"
    key_id: str                     # Razorpay public key (safe to expose)


class OrderResponse(BaseModel):
    """Full order details"""

    id: UUID
    user_id: UUID
    book_id: UUID
    format: str
    amount: int
    taxable_amount: int
    gst_rate_percent: int
    gst_amount: int
    total_amount: int
    currency: str
    razorpay_order_id: str
    razorpay_payment_id: str | None
    status: str
    paid_at: datetime | None
    created_at: datetime
    whatsapp_number: str | None = None

    model_config = {"from_attributes": True}
