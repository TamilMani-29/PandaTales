# Orders & Checkout API

**Base Path:** `/api/v1/orders`  
**Version:** 1.0  
**Authentication:** Required (JWT Bearer Token)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Order Flow](#order-flow)
3. [Endpoints](#endpoints)
4. [Data Models](#data-models)
5. [Pricing Logic](#pricing-logic)
6. [Error Codes](#error-codes)

---

## Overview

The Orders & Checkout API handles cart management, order creation, order tracking, and order history for Panda Tales.

### Features
- Shopping cart management
- Order creation for digital and physical books
- Multiple product formats (Digital, Softcover, Hardcover)
- Shipping address management
- Order status tracking
- Order history and details
- Reorder functionality

---

## Order Flow

```
┌──────┐                                          ┌──────┐
│Client│                                          │Server│
└──┬───┘                                          └──┬───┘
   │                                                 │
   │ POST /cart/items                                │
   │ {bookId, format: "digital"}                     │
   ├────────────────────────────────────────────────►│
   │                                                 │
   │ ◄───────────────────────────────────────────────┤
   │ {cartId, items, totalPrice}                     │
   │                                                 │
   │ GET /cart                                       │
   ├────────────────────────────────────────────────►│
   │                                                 │
   │ ◄───────────────────────────────────────────────┤
   │ {items: [...], totalPrice, shipping}            │
   │                                                 │
   │ POST /orders/checkout                           │
   │ {cartId, addressId, paymentMethodId}            │
   ├────────────────────────────────────────────────►│
   │                                                 │
   │                                            [Create Order]
   │                                            [Process Payment]
   │                                                 │
   │ ◄───────────────────────────────────────────────┤
   │ {orderId, status, total, paymentIntent}         │
   │                                                 │
   │ [Payment Confirmation]                          │
   │                                                 │
   │ POST /orders/{orderId}/confirm                  │
   ├────────────────────────────────────────────────►│
   │                                                 │
   │ ◄───────────────────────────────────────────────┤
   │ {orderId, status: "confirmed",                  │
   │  downloadUrl, trackingNumber}                   │
```

---

## Endpoints

### 1. Get Cart

**Endpoint:** `GET /api/v1/orders/cart`

**Description:** Get current user's shopping cart.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "cartId": "cart_abc123",
    "items": [
      {
        "id": "item_001",
        "bookId": "book_xyz789",
        "book": {
          "title": "Emma's First Adventure",
          "childName": "Emma",
          "coverImage": "https://cdn.pandatales.com/books/book_xyz789_cover.jpg"
        },
        "format": "digital",
        "quantity": 1,
        "unitPrice": 19.99,
        "totalPrice": 19.99,
        "addedAt": "2026-02-14T10:30:00Z"
      },
      {
        "id": "item_002",
        "bookId": "book_abc456",
        "book": {
          "title": "Oliver's Magical Quest",
          "childName": "Oliver",
          "coverImage": "https://cdn.pandatales.com/books/book_abc456_cover.jpg"
        },
        "format": "hardcover",
        "quantity": 1,
        "unitPrice": 39.99,
        "totalPrice": 39.99,
        "addedAt": "2026-02-14T10:32:00Z"
      }
    ],
    "summary": {
      "itemCount": 2,
      "subtotal": 59.98,
      "shipping": 5.99,
      "tax": 5.40,
      "discount": 0.00,
      "total": 71.37
    },
    "updatedAt": "2026-02-14T10:32:00Z"
  }
}
```

---

### 2. Add to Cart

**Endpoint:** `POST /api/v1/orders/cart/items`

**Description:** Add a book to the shopping cart.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "bookId": "book_xyz789",
  "format": "digital",
  "quantity": 1
}
```

**Format Options:**
- `digital` - Digital PDF download
- `softcover` - Softcover printed book
- `hardcover` - Hardcover printed book

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Item added to cart",
  "data": {
    "cartId": "cart_abc123",
    "itemId": "item_001",
    "itemCount": 1,
    "total": 19.99
  }
}
```

**Errors:**
- `400` - Invalid book ID or format
- `404` - Book not found
- `409` - Book already in cart

---

### 3. Update Cart Item

**Endpoint:** `PATCH /api/v1/orders/cart/items/{itemId}`

**Description:** Update cart item (change format or quantity).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `itemId` - Cart item ID

**Request Body:**
```json
{
  "format": "hardcover",
  "quantity": 2
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Cart item updated",
  "data": {
    "itemId": "item_001",
    "format": "hardcover",
    "quantity": 2,
    "totalPrice": 79.98
  }
}
```

---

### 4. Remove from Cart

**Endpoint:** `DELETE /api/v1/orders/cart/items/{itemId}`

**Description:** Remove an item from the cart.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `itemId` - Cart item ID

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Item removed from cart",
  "data": {
    "itemCount": 1,
    "total": 39.99
  }
}
```

---

### 5. Clear Cart

**Endpoint:** `DELETE /api/v1/orders/cart`

**Description:** Remove all items from the cart.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Cart cleared"
}
```

---

### 6. Apply Discount Code

**Endpoint:** `POST /api/v1/orders/cart/discount`

**Description:** Apply a discount/promo code to the cart.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "code": "WELCOME10"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Discount applied",
  "data": {
    "code": "WELCOME10",
    "discountType": "percentage",
    "discountValue": 10,
    "discountAmount": 5.99,
    "newTotal": 65.38
  }
}
```

**Errors:**
- `400` - Invalid or expired code
- `409` - Code already applied

---

### 7. Remove Discount Code

**Endpoint:** `DELETE /api/v1/orders/cart/discount`

**Description:** Remove applied discount code.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`

---

### 8. Calculate Shipping

**Endpoint:** `POST /api/v1/orders/cart/calculate-shipping`

**Description:** Calculate shipping cost for physical books.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "addressId": "addr_123abc"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "shipping": {
      "standard": {
        "cost": 5.99,
        "estimatedDays": "7-10",
        "carrier": "USPS"
      },
      "express": {
        "cost": 12.99,
        "estimatedDays": "3-5",
        "carrier": "FedEx"
      },
      "overnight": {
        "cost": 24.99,
        "estimatedDays": "1-2",
        "carrier": "FedEx"
      }
    },
    "default": "standard"
  }
}
```

---

### 9. Initiate Checkout

**Endpoint:** `POST /api/v1/orders/checkout`

**Description:** Create an order from cart and initiate payment.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "cartId": "cart_abc123",
  "shippingAddressId": "addr_123abc",
  "shippingMethod": "standard",
  "billingAddressId": "addr_123abc",
  "saveAddress": true
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Order created successfully",
  "data": {
    "orderId": "order_xyz789",
    "orderNumber": "SB-2026-000123",
    "status": "pending_payment",
    "items": [
      {
        "bookId": "book_xyz789",
        "title": "Emma's First Adventure",
        "format": "digital",
        "price": 19.99
      }
    ],
    "summary": {
      "subtotal": 19.99,
      "shipping": 0.00,
      "tax": 1.80,
      "discount": 0.00,
      "total": 21.79
    },
    "paymentIntent": {
      "clientSecret": "pi_123abc_secret_xyz",
      "amount": 2179,
      "currency": "usd"
    },
    "createdAt": "2026-02-14T10:35:00Z"
  }
}
```

**Note:** Returns Stripe payment intent for frontend to complete payment.

---

### 10. Get Order Details

**Endpoint:** `GET /api/v1/orders/{orderId}`

**Description:** Get details of a specific order.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `orderId` - Order ID

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "order_xyz789",
    "orderNumber": "SB-2026-000123",
    "status": "completed",
    "items": [
      {
        "id": "item_001",
        "bookId": "book_xyz789",
        "book": {
          "title": "Emma's First Adventure",
          "childName": "Emma",
          "coverImage": "..."
        },
        "format": "digital",
        "quantity": 1,
        "unitPrice": 19.99,
        "totalPrice": 19.99,
        "downloadUrl": "https://cdn.pandatales.com/downloads/..."
      }
    ],
    "summary": {
      "subtotal": 19.99,
      "shipping": 0.00,
      "tax": 1.80,
      "discount": 0.00,
      "total": 21.79
    },
    "shippingAddress": {
      "firstName": "John",
      "lastName": "Doe",
      "addressLine1": "123 Main St",
      "city": "New York",
      "state": "NY",
      "postalCode": "10001",
      "country": "US"
    },
    "shippingMethod": "standard",
    "trackingNumber": null,
    "estimatedDelivery": null,
    "payment": {
      "method": "card",
      "last4": "4242",
      "brand": "visa",
      "status": "paid"
    },
    "timeline": [
      {
        "status": "pending_payment",
        "timestamp": "2026-02-14T10:35:00Z"
      },
      {
        "status": "payment_confirmed",
        "timestamp": "2026-02-14T10:36:00Z"
      },
      {
        "status": "completed",
        "timestamp": "2026-02-14T10:36:00Z"
      }
    ],
    "createdAt": "2026-02-14T10:35:00Z",
    "updatedAt": "2026-02-14T10:36:00Z"
  }
}
```

**Errors:**
- `404` - Order not found
- `403` - Not authorized to access this order

---

### 11. List Orders

**Endpoint:** `GET /api/v1/orders`

**Description:** Get user's order history.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (integer, default: 1)
- `pageSize` (integer, default: 20)
- `status` (string): Filter by status
- `sort` (string, default: 'newest'): 'newest', 'oldest'

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "order_xyz789",
        "orderNumber": "SB-2026-000123",
        "status": "completed",
        "itemCount": 2,
        "total": 71.37,
        "createdAt": "2026-02-14T10:35:00Z",
        "items": [
          {
            "bookTitle": "Emma's First Adventure",
            "format": "digital",
            "coverImage": "..."
          }
        ]
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "totalPages": 1,
      "totalItems": 5,
      "hasNext": false,
      "hasPrev": false
    },
    "summary": {
      "totalOrders": 5,
      "totalSpent": 245.67,
      "pendingOrders": 0
    }
  }
}
```

---

### 12. Cancel Order

**Endpoint:** `POST /api/v1/orders/{orderId}/cancel`

**Description:** Cancel an order (only if not yet shipped).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `orderId` - Order ID

**Request Body:**
```json
{
  "reason": "Changed my mind"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Order cancelled successfully",
  "data": {
    "orderId": "order_xyz789",
    "status": "cancelled",
    "refund": {
      "amount": 21.79,
      "status": "pending",
      "estimatedDate": "2026-02-17T00:00:00Z"
    }
  }
}
```

**Errors:**
- `400` - Order cannot be cancelled (already shipped)
- `404` - Order not found

---

### 13. Reorder

**Endpoint:** `POST /api/v1/orders/{orderId}/reorder`

**Description:** Create a new order with same items as previous order.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `orderId` - Original order ID

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Items added to cart",
  "data": {
    "cartId": "cart_new123",
    "itemCount": 2
  }
}
```

---

### 14. Download Invoice

**Endpoint:** `GET /api/v1/orders/{orderId}/invoice`

**Description:** Download order invoice as PDF.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `orderId` - Order ID

**Response:** `200 OK`
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="invoice-SB-2026-000123.pdf"

[PDF Binary Data]
```

---

### 15. Request Refund

**Endpoint:** `POST /api/v1/orders/{orderId}/refund`

**Description:** Request a refund for an order.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `orderId` - Order ID

**Request Body:**
```json
{
  "reason": "Not satisfied with quality",
  "items": ["item_001"],
  "amount": 19.99
}
```

**Response:** `202 Accepted`
```json
{
  "success": true,
  "message": "Refund request submitted",
  "data": {
    "refundId": "refund_abc123",
    "status": "pending_review",
    "amount": 19.99,
    "estimatedProcessingTime": "3-5 business days"
  }
}
```

---

## Data Models

### Order Model
```python
class Order:
    id: str
    order_number: str  # SB-2026-000123
    user_id: str
    status: str
    items: List[OrderItem]
    subtotal: float
    shipping: float
    tax: float
    discount: float
    total: float
    shipping_address: Optional[Address]
    billing_address: Optional[Address]
    shipping_method: Optional[str]
    tracking_number: Optional[str]
    estimated_delivery: Optional[datetime]
    payment_intent_id: Optional[str]
    payment_status: str
    created_at: datetime
    updated_at: datetime
    cancelled_at: Optional[datetime]
    completed_at: Optional[datetime]
```

### Order Item Model
```python
class OrderItem:
    id: str
    order_id: str
    book_id: str
    format: str  # 'digital', 'softcover', 'hardcover'
    quantity: int
    unit_price: float
    total_price: float
    download_url: Optional[str]  # For digital purchases
```

### Cart Model
```python
class Cart:
    id: str
    user_id: str
    items: List[CartItem]
    discount_code: Optional[str]
    discount_amount: float
    created_at: datetime
    updated_at: datetime
```

### Cart Item Model
```python
class CartItem:
    id: str
    cart_id: str
    book_id: str
    format: str
    quantity: int
    unit_price: float
    total_price: float
    added_at: datetime
```

---

## Pricing Logic

### Product Pricing

**Digital Books:**
- Base price: $19.99
- No shipping
- Instant delivery

**Softcover Books:**
- Base price: $29.99
- Shipping calculated by location
- 5-7 business days production + shipping

**Hardcover Books:**
- Base price: $39.99
- Shipping calculated by location
- 7-10 business days production + shipping

### Shipping Calculation

**Domestic (US):**
- Standard: $5.99 (7-10 days)
- Express: $12.99 (3-5 days)
- Overnight: $24.99 (1-2 days)

**International:**
- Standard: $19.99 (14-21 days)
- Express: $39.99 (7-10 days)

**Free Shipping:**
- Orders over $75 (US only)
- Digital-only orders

### Tax Calculation

```python
def calculate_tax(subtotal: float, state: str) -> float:
    """
    Calculate sales tax based on state
    """
    TAX_RATES = {
        'CA': 0.0725,  # California
        'NY': 0.04,    # New York
        'TX': 0.0625,  # Texas
        # ... other states
    }
    
    rate = TAX_RATES.get(state, 0)
    return round(subtotal * rate, 2)
```

### Discount Codes

**Types:**
- Percentage: 10%, 20%, etc.
- Fixed Amount: $5, $10, etc.
- Free Shipping

**Validation:**
- Expiry date
- Minimum order amount
- Usage limit per customer
- Total usage limit

---

## Order Status Flow

```
pending_payment
    ↓
payment_confirmed
    ↓
processing (for physical books)
    ↓
shipped (for physical books)
    ↓
delivered / completed
```

**Alternate Flows:**
```
pending_payment → cancelled
processing → cancelled (with refund)
completed → refund_requested → refunded
```

---

## Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `ORDER_NOT_FOUND` | 404 | Order not found |
| `ORDER_UNAUTHORIZED` | 403 | Not authorized to access order |
| `CART_EMPTY` | 400 | Cannot checkout with empty cart |
| `INVALID_DISCOUNT_CODE` | 400 | Discount code invalid or expired |
| `SHIPPING_ADDRESS_REQUIRED` | 400 | Shipping address required for physical books |
| `PAYMENT_FAILED` | 402 | Payment processing failed |
| `CANNOT_CANCEL_ORDER` | 400 | Order cannot be cancelled |
| `ITEM_NOT_IN_CART` | 404 | Cart item not found |

---

## Testing

### Test Cases

1. **Cart Management**
   - ✅ Add to cart
   - ✅ Update quantity
   - ✅ Remove from cart
   - ✅ Clear cart

2. **Checkout**
   - ✅ Digital-only order
   - ✅ Physical book order
   - ✅ Mixed order (digital + physical)
   - ✅ Apply discount code
   - ✅ Shipping calculation

3. **Order Management**
   - ✅ Create order
   - ✅ Get order details
   - ✅ List orders
   - ✅ Cancel order
   - ✅ Reorder

4. **Pricing**
   - ✅ Subtotal calculation
   - ✅ Tax calculation
   - ✅ Shipping calculation
   - ✅ Discount application
