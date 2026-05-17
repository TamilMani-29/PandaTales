"""Pydantic schemas for digital book catalog APIs."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class DigitalBookCreateRequest(BaseModel):
    """Payload for creating a digital book catalog entry."""

    book_name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category_id: int | None = Field(None, ge=1)
    emoji: str | None = Field(None, max_length=16)
    total_pages: int | None = Field(None, ge=1)
    book_type: str = Field(..., min_length=1, max_length=50)
    theme: str = Field(..., min_length=1, max_length=50)
    language: str = Field("english", min_length=1, max_length=50)
    genre: str = Field(..., min_length=1, max_length=100)
    price: Decimal | None = Field(None, ge=0)
    rating: float | None = Field(None, ge=0, le=5)
    total_ratings: int | None = Field(None, ge=0)
    download_count: int | None = Field(None, ge=0)
    is_bestseller: bool = False
    is_personalized: bool = False


class DigitalBookUpdateRequest(BaseModel):
    """Payload for partially updating a digital book (all fields optional)."""

    book_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    category_id: int | None = Field(None, ge=1)
    emoji: str | None = Field(None, max_length=16)
    total_pages: int | None = Field(None, ge=1)
    book_type: str | None = Field(None, min_length=1, max_length=50)
    theme: str | None = Field(None, min_length=1, max_length=50)
    language: str | None = Field(None, min_length=1, max_length=50)
    genre: str | None = Field(None, min_length=1, max_length=100)
    price: Decimal | None = Field(None, ge=0)
    rating: float | None = Field(None, ge=0, le=5)
    total_ratings: int | None = Field(None, ge=0)
    download_count: int | None = Field(None, ge=0)
    is_bestseller: bool | None = None
    is_personalized: bool | None = None


class DigitalBookCategoryResponse(BaseModel):
    """Response for category assignment operation."""

    book_id: int
    category_id: int


class BookCategoryCreateRequest(BaseModel):
    """Payload for creating/updating category metadata."""

    category_id: int | None = Field(None, ge=1)
    name: str = Field(..., min_length=1, max_length=120)
    tags: list[str] | None = None
    label: str | None = Field(None, max_length=80, description="Short badge label shown top-right on card (e.g. PERSONALIZED, NEW, BESTSELLER)")
    description: str | None = None
    emoji: str | None = Field(None, max_length=16)
    color: str | None = Field(None, max_length=32)
    grad: str | None = None
    personalized: bool = False
    is_active: bool = True


class BookCategoryResponse(BaseModel):
    """Category metadata response."""

    id: int
    category_id: int
    name: str
    tags: list[str]
    personalized_tag: str | None
    label: str | None
    description: str | None
    emoji: str | None
    color: str | None
    grad: str | None
    personalized: bool
    is_active: bool


class BookAttributeOptionCreateRequest(BaseModel):
    """Payload for adding admin-managed dropdown options."""

    option_type: str = Field(..., pattern="^(book_type|theme|language|genre)$")
    value: str = Field(..., min_length=1, max_length=100)


class DigitalBookResponse(BaseModel):
    """Response model for digital book item."""

    id: int
    book_name: str
    description: str | None
    category_id: int | None
    category: int | None       # alias for category_id
    category_name: str | None
    category_tag: str | None
    category_tags: list[str]
    category_description: str | None
    emoji: str | None
    is_bestseller: bool
    is_personalized: bool
    personalized_kind: str | None
    cover_image_url: str | None
    cover_image_presigned_url: str | None
    front_image_url: str | None
    front_image_presigned_url: str | None
    back_image_url: str | None
    back_image_presigned_url: str | None
    book_url: str | None
    total_pages: int | None
    book_type: str | None
    theme: str | None
    language: str | None
    genre_id: int | None
    genre_name: str | None
    price: float | None
    rating: float
    total_ratings: int
    download_count: int
    created_at: datetime
    updated_at: datetime
    title: str
    desc: str | None
    pages: int | None
    age: str | None
    rat: float
    rev: int


class DigitalBookPurchaseRequest(BaseModel):
    """Payload for digital book purchase."""

    book_id: int = Field(..., ge=1)
    delivery_method: str = Field("local", pattern="^(local|email|whatsapp)$")
    delivery_contact: str = Field(..., min_length=3, max_length=120)


class DigitalBookPaymentCreateRequest(BaseModel):
    """Payload to start checkout and create a Razorpay order for digital book."""

    book_id: int = Field(..., ge=1)
    delivery_method: str = Field("local", pattern="^(local|email|whatsapp)$")
    delivery_contact: str = Field(..., min_length=3, max_length=120)


class DigitalBookPaymentCreateResponse(BaseModel):
    """Response returned after creating Razorpay order."""

    order_id: int
    user_id: UUID
    book_id: int
    amount: int
    taxable_amount: int
    gst_rate_percent: int
    gst_amount: int
    total_amount: int
    currency: str
    key_id: str
    razorpay_order_id: str
    payment_status: str
    delivery_method: str
    delivery_contact: str


class DigitalBookPaymentVerifyRequest(BaseModel):
    """Razorpay callback payload to verify payment signature."""

    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class DigitalBookPaymentHistoryResponse(BaseModel):
    """Payment history item for digital purchases."""

    order_id: int
    user_id: UUID
    book_id: int
    book_name: str
    amount: int
    taxable_amount: int
    gst_rate_percent: int
    gst_amount: int
    total_amount: int
    currency: str
    payment_status: str
    status: str
    razorpay_order_id: str | None
    razorpay_payment_id: str | None
    delivery_method: str
    delivery_contact: str
    delivery_status: str
    payment_error: str | None
    created_at: datetime
    paid_at: datetime | None
    delivery_sent_at: datetime | None


class DigitalBookPurchaseResponse(BaseModel):
    """Response after digital book purchase is created."""

    order_id: int
    book_id: int
    status: str
    delivery_method: str
    delivery_contact: str


class DigitalBookListResponse(BaseModel):
    """Response model for listing digital books."""

    books: list[DigitalBookResponse]

