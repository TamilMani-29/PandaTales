# Payment Processing API

**Base Path:** `/api/v1/payments`  
**Version:** 1.0  
**Authentication:** Required (JWT Bearer Token)  
**Payment Provider:** Stripe

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Payment Flow](#payment-flow)
3. [Endpoints](#endpoints)
4. [Webhooks](#webhooks)
5. [Data Models](#data-models)
6. [Security](#security)
7. [Error Codes](#error-codes)

---

## Overview

The Payment Processing API integrates with Stripe to handle secure payment processing for Panda Tales.

### Features
- Stripe Payment Intents integration
- Credit/Debit card payments
- Apple Pay & Google Pay support
- Secure card tokenization
- Payment method management
- Refund processing
- Webhook handling for async events
- Invoice generation

---

## Payment Flow

### Standard Payment Flow

```
┌──────┐                  ┌──────┐                 ┌────────┐
│Client│                  │Server│                 │ Stripe │
└──┬───┘                  └──┬───┘                 └───┬────┘
   │                         │                         │
   │ POST /checkout          │                         │
   ├────────────────────────►│                         │
   │                         │                         │
   │                         │ Create Payment Intent   │
   │                         ├────────────────────────►│
   │                         │                         │
   │                         │ ◄───────────────────────┤
   │                         │ {clientSecret}          │
   │                         │                         │
   │ ◄───────────────────────┤                         │
   │ {clientSecret, orderId} │                         │
   │                         │                         │
   │ [User enters card]      │                         │
   │                         │                         │
   │ Confirm Payment         │                         │
   │ (via Stripe.js)         │                         │
   ├─────────────────────────┼────────────────────────►│
   │                         │                         │
   │                         │    [Webhook: payment    │
   │                         │     succeeded]          │
   │                         │ ◄───────────────────────┤
   │                         │                         │
   │                         │ [Update Order Status]   │
   │                         │                         │
   │ ◄───────────────────────┤                         │
   │ {status: success}       │                         │
   │                         │                         │
   │ GET /orders/{orderId}   │                         │
   ├────────────────────────►│                         │
   │                         │                         │
   │ ◄───────────────────────┤                         │
   │ {order: completed}      │                         │
```

---

## Endpoints

### 1. Create Payment Intent

**Endpoint:** `POST /api/v1/payments/intent`

**Description:** Create a Stripe payment intent for an order.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "orderId": "order_xyz789",
  "amount": 2179,
  "currency": "usd",
  "paymentMethodTypes": ["card", "apple_pay", "google_pay"]
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "paymentIntentId": "pi_3MtwBwLkdIwHu7ix0SNj0cFn",
    "clientSecret": "pi_3MtwBwLkdIwHu7ix0SNj0cFn_secret_XYZ",
    "amount": 2179,
    "currency": "usd",
    "status": "requires_payment_method",
    "orderId": "order_xyz789"
  }
}
```

**Note:** This is typically called automatically during checkout. Frontend uses `clientSecret` with Stripe.js to collect payment.

---

### 2. Confirm Payment

**Endpoint:** `POST /api/v1/payments/confirm`

**Description:** Confirm payment after user submits card (alternative to webhook).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "paymentIntentId": "pi_3MtwBwLkdIwHu7ix0SNj0cFn",
  "orderId": "order_xyz789"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Payment confirmed",
  "data": {
    "orderId": "order_xyz789",
    "paymentStatus": "succeeded",
    "amount": 2179,
    "last4": "4242",
    "brand": "visa"
  }
}
```

**Errors:**
- `400` - Payment intent not found
- `402` - Payment failed

---

### 3. Get Payment Status

**Endpoint:** `GET /api/v1/payments/status/{paymentIntentId}`

**Description:** Check status of a payment intent.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `paymentIntentId` - Stripe Payment Intent ID

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "paymentIntentId": "pi_3MtwBwLkdIwHu7ix0SNj0cFn",
    "status": "succeeded",
    "amount": 2179,
    "currency": "usd",
    "orderId": "order_xyz789",
    "created": "2026-02-14T10:35:00Z"
  }
}
```

**Payment Intent Statuses:**
- `requires_payment_method` - Awaiting payment method
- `requires_confirmation` - Payment method provided, needs confirmation
- `requires_action` - Requires 3D Secure or similar
- `processing` - Payment being processed
- `succeeded` - Payment successful
- `canceled` - Payment canceled
- `requires_capture` - Payment authorized, awaiting capture

---

### 4. Save Payment Method

**Endpoint:** `POST /api/v1/payments/methods`

**Description:** Save a payment method for future use.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "paymentMethodId": "pm_1MtwBwLkdIwHu7ix0KSYRZKS",
  "setAsDefault": true
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Payment method saved",
  "data": {
    "id": "pm_1MtwBwLkdIwHu7ix0KSYRZKS",
    "type": "card",
    "card": {
      "brand": "visa",
      "last4": "4242",
      "expMonth": 12,
      "expYear": 2027
    },
    "isDefault": true,
    "created": "2026-02-14T10:35:00Z"
  }
}
```

---

### 5. List Payment Methods

**Endpoint:** `GET /api/v1/payments/methods`

**Description:** Get all saved payment methods for the user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "methods": [
      {
        "id": "pm_1MtwBwLkdIwHu7ix0KSYRZKS",
        "type": "card",
        "card": {
          "brand": "visa",
          "last4": "4242",
          "expMonth": 12,
          "expYear": 2027
        },
        "isDefault": true,
        "created": "2026-01-15T10:30:00Z"
      },
      {
        "id": "pm_2MtwBwLkdIwHu7ix1KSYRZKS",
        "type": "card",
        "card": {
          "brand": "mastercard",
          "last4": "5555",
          "expMonth": 6,
          "expYear": 2028
        },
        "isDefault": false,
        "created": "2026-02-01T14:20:00Z"
      }
    ],
    "totalCount": 2
  }
}
```

---

### 6. Delete Payment Method

**Endpoint:** `DELETE /api/v1/payments/methods/{paymentMethodId}`

**Description:** Remove a saved payment method.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `paymentMethodId` - Stripe Payment Method ID

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Payment method deleted"
}
```

**Errors:**
- `404` - Payment method not found
- `400` - Cannot delete default payment method (set another as default first)

---

### 7. Set Default Payment Method

**Endpoint:** `POST /api/v1/payments/methods/{paymentMethodId}/default`

**Description:** Set a payment method as default.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `paymentMethodId` - Stripe Payment Method ID

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Default payment method updated"
}
```

---

### 8. Create Refund

**Endpoint:** `POST /api/v1/payments/refunds`

**Description:** Process a refund for a payment (admin or system use).

**Headers:**
```
Authorization: Bearer <access_token>
X-Admin-Key: <admin_key>
```

**Request Body:**
```json
{
  "paymentIntentId": "pi_3MtwBwLkdIwHu7ix0SNj0cFn",
  "amount": 2179,
  "reason": "requested_by_customer"
}
```

**Reason Options:**
- `duplicate` - Duplicate charge
- `fraudulent` - Fraudulent transaction
- `requested_by_customer` - Customer request

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Refund processed",
  "data": {
    "refundId": "re_3MtwBwLkdIwHu7ix0SNj0cFn",
    "amount": 2179,
    "currency": "usd",
    "status": "succeeded",
    "reason": "requested_by_customer",
    "estimatedArrival": "2026-02-17T00:00:00Z"
  }
}
```

---

### 9. List Transactions

**Endpoint:** `GET /api/v1/payments/transactions`

**Description:** Get payment transaction history.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (integer, default: 1)
- `pageSize` (integer, default: 20)
- `status` (string): Filter by status
- `startDate`, `endDate` (ISO dates): Date range

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": "txn_abc123",
        "paymentIntentId": "pi_3MtwBwLkdIwHu7ix0SNj0cFn",
        "orderId": "order_xyz789",
        "orderNumber": "SB-2026-000123",
        "amount": 2179,
        "currency": "usd",
        "status": "succeeded",
        "paymentMethod": {
          "type": "card",
          "brand": "visa",
          "last4": "4242"
        },
        "created": "2026-02-14T10:35:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "totalPages": 1,
      "totalItems": 8
    },
    "summary": {
      "totalTransactions": 8,
      "totalAmount": 187.65,
      "successfulTransactions": 7,
      "failedTransactions": 1
    }
  }
}
```

---

### 10. Get Transaction Details

**Endpoint:** `GET /api/v1/payments/transactions/{transactionId}`

**Description:** Get detailed information about a transaction.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `transactionId` - Transaction ID

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "txn_abc123",
    "paymentIntentId": "pi_3MtwBwLkdIwHu7ix0SNj0cFn",
    "orderId": "order_xyz789",
    "amount": 2179,
    "currency": "usd",
    "status": "succeeded",
    "paymentMethod": {
      "id": "pm_1MtwBwLkdIwHu7ix0KSYRZKS",
      "type": "card",
      "brand": "visa",
      "last4": "4242",
      "expMonth": 12,
      "expYear": 2027
    },
    "billing": {
      "name": "John Doe",
      "email": "john@example.com",
      "address": {
        "line1": "123 Main St",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "US"
      }
    },
    "fees": {
      "stripeFee": 93,
      "applicationFee": 0,
      "net": 2086
    },
    "created": "2026-02-14T10:35:00Z",
    "updated": "2026-02-14T10:36:00Z"
  }
}
```

---

### 11. Retry Failed Payment

**Endpoint:** `POST /api/v1/payments/{paymentIntentId}/retry`

**Description:** Retry a failed payment with same or different payment method.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `paymentIntentId` - Original Payment Intent ID

**Request Body:**
```json
{
  "paymentMethodId": "pm_2MtwBwLkdIwHu7ix1KSYRZKS"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "paymentIntentId": "pi_3MtwBwLkdIwHu7ix0SNj0cFn",
    "clientSecret": "pi_3MtwBwLkdIwHu7ix0SNj0cFn_secret_NEW",
    "status": "requires_confirmation"
  }
}
```

---

## Webhooks

### Webhook Endpoint

**Endpoint:** `POST /api/v1/payments/webhooks/stripe`

**Description:** Stripe webhook handler for async payment events.

**Headers:**
```
Stripe-Signature: t=1234567890,v1=abc123def456...
```

**Request Body:** (Raw Stripe webhook payload)

**Handled Events:**

1. **payment_intent.succeeded**
   - Update order status to "payment_confirmed"
   - Send confirmation email
   - Unlock book downloads

2. **payment_intent.payment_failed**
   - Update order status to "payment_failed"
   - Send failure notification
   - Provide retry options

3. **payment_intent.canceled**
   - Update order status to "canceled"
   - Release inventory (if applicable)

4. **charge.refunded**
   - Update order status to "refunded"
   - Revoke download access
   - Send refund confirmation email

5. **payment_method.attached**
   - Save payment method to user account

6. **payment_method.detached**
   - Remove payment method from user account

**Response:** `200 OK`
```json
{
  "received": true
}
```

### Webhook Security

```python
import stripe

@app.post("/api/v1/payments/webhooks/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhooks
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        await handle_payment_succeeded(payment_intent)
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        await handle_payment_failed(payment_intent)
    
    return {"received": True}
```

---

## Data Models

### Payment Intent Model
```python
class PaymentIntent:
    id: str  # Stripe Payment Intent ID
    order_id: str
    user_id: str
    amount: int  # In cents
    currency: str
    status: str
    payment_method_id: Optional[str]
    client_secret: str
    created_at: datetime
    updated_at: datetime
```

### Payment Method Model
```python
class PaymentMethod:
    id: str  # Stripe Payment Method ID
    user_id: str
    type: str  # 'card', 'apple_pay', 'google_pay'
    card: Optional[CardDetails]
    is_default: bool
    created_at: datetime
```

### Card Details Model
```python
class CardDetails:
    brand: str  # 'visa', 'mastercard', etc.
    last4: str
    exp_month: int
    exp_year: int
    country: Optional[str]
```

### Transaction Model
```python
class Transaction:
    id: str
    payment_intent_id: str
    order_id: str
    user_id: str
    amount: int
    currency: str
    status: str
    payment_method_type: str
    stripe_fee: int
    net_amount: int
    created_at: datetime
    updated_at: datetime
```

### Refund Model
```python
class Refund:
    id: str  # Stripe Refund ID
    payment_intent_id: str
    order_id: str
    amount: int
    currency: str
    reason: str
    status: str
    created_at: datetime
```

---

## Security

### PCI Compliance

Panda Tales follows PCI DSS compliance:

1. **Never Store Card Data**
   - All card data handled by Stripe
   - Only store Stripe tokens/IDs
   - No card numbers in logs

2. **HTTPS Only**
   - All payment endpoints require HTTPS
   - TLS 1.2+ enforced

3. **Webhook Verification**
   - All webhooks verified with signature
   - Replay attack prevention

4. **Access Control**
   - Payment methods tied to user accounts
   - Users can only access their own payment data

### Stripe API Keys

```python
# Environment Variables
STRIPE_PUBLIC_KEY=pk_live_...    # Frontend (public)
STRIPE_SECRET_KEY=sk_live_...    # Backend (secret)
STRIPE_WEBHOOK_SECRET=whsec_...  # Webhook verification
```

**Key Management:**
- Secret keys never exposed to frontend
- Separate keys for test/production
- Rotate keys every 90 days
- Monitor for suspicious activity

---

## Error Codes

### Stripe Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `card_declined` | 402 | Card was declined |
| `expired_card` | 402 | Card has expired |
| `incorrect_cvc` | 402 | CVC is incorrect |
| `insufficient_funds` | 402 | Insufficient funds |
| `processing_error` | 500 | Payment processing error |
| `rate_limit` | 429 | Too many requests |

### Application Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `PAYMENT_INTENT_NOT_FOUND` | 404 | Payment intent not found |
| `PAYMENT_METHOD_NOT_FOUND` | 404 | Payment method not found |
| `PAYMENT_ALREADY_PROCESSED` | 409 | Payment already completed |
| `REFUND_FAILED` | 500 | Refund processing failed |
| `INVALID_AMOUNT` | 400 | Invalid payment amount |
| `WEBHOOK_VERIFICATION_FAILED` | 400 | Webhook signature invalid |

---

## Testing

### Test Cards (Stripe)

**Successful Payments:**
```
4242 4242 4242 4242  # Visa
5555 5555 5555 4444  # Mastercard
3782 822463 10005    # American Express
```

**Payment Failures:**
```
4000 0000 0000 0002  # Declined
4000 0000 0000 9995  # Insufficient funds
4000 0000 0000 0069  # Expired card
4000 0000 0000 0127  # Incorrect CVC
```

**3D Secure Required:**
```
4000 0025 0000 3155  # Requires authentication
```

### Test Cases

1. **Payment Flow**
   - ✅ Create payment intent
   - ✅ Successful payment
   - ✅ Failed payment
   - ✅ 3D Secure authentication
   - ✅ Payment retry

2. **Payment Methods**
   - ✅ Save payment method
   - ✅ List payment methods
   - ✅ Delete payment method
   - ✅ Set default method

3. **Refunds**
   - ✅ Full refund
   - ✅ Partial refund
   - ✅ Refund failure

4. **Webhooks**
   - ✅ Payment succeeded webhook
   - ✅ Payment failed webhook
   - ✅ Refund webhook
   - ✅ Webhook signature verification

---

## Implementation Notes

### Stripe SDK Setup

```python
# requirements.txt
stripe>=5.0.0

# app/core/config.py
import stripe
from app.core.settings import settings

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = "2023-10-16"
```

### Frontend Integration

```typescript
// client/lib/stripe.ts
import { loadStripe } from '@stripe/stripe-js';

export const stripePromise = loadStripe(
  process.env.NEXT_PUBLIC_STRIPE_PUBLIC_KEY!
);

// Payment form
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';

const PaymentForm = () => {
  const stripe = useStripe();
  const elements = useElements();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const { clientSecret } = await createPaymentIntent();
    
    const { error, paymentIntent } = await stripe.confirmCardPayment(
      clientSecret,
      {
        payment_method: {
          card: elements.getElement(CardElement),
          billing_details: { name: 'John Doe' }
        }
      }
    );
    
    if (error) {
      // Handle error
    } else if (paymentIntent.status === 'succeeded') {
      // Payment successful
    }
  };
};
```

---

## Monitoring & Analytics

### Key Metrics

- Payment success rate
- Average transaction value
- Failed payment reasons
- Refund rate
- Processing time
- Webhook delivery success

### Stripe Dashboard

Monitor via Stripe Dashboard:
- Real-time transactions
- Payment success/failure rates
- Dispute management
- Revenue reports
- Customer insights
