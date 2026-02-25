# Story Bloom - Backend API Design Overview

**Version:** 1.0  
**Last Updated:** February 14, 2026  
**Technology Stack:** FastAPI, Python 3.11+, PostgreSQL, MinIO/S3

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [API Modules](#api-modules)
3. [Technology Stack](#technology-stack)
4. [Common Patterns](#common-patterns)
5. [Security & Authentication](#security--authentication)
6. [Error Handling](#error-handling)
7. [API Versioning](#api-versioning)

---

## 🏗 Architecture Overview

Story Bloom backend follows a modular microservices-ready architecture:

```
┌─────────────┐
│   Client    │
│  (Next.js)  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         FastAPI Gateway/Backend         │
├─────────────────────────────────────────┤
│  ┌─────────┐  ┌──────────┐  ┌────────┐│
│  │  Auth   │  │  Books   │  │ Orders ││
│  │ Module  │  │  Module  │  │ Module ││
│  └─────────┘  └──────────┘  └────────┘│
│  ┌─────────┐  ┌──────────┐  ┌────────┐│
│  │  User   │  │Generation│  │Payment ││
│  │ Module  │  │  Module  │  │ Module ││
│  └─────────┘  └──────────┘  └────────┘│
└─────────────────────────────────────────┘
       │         │          │
       ▼         ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────┐
│PostgreSQL│ │  MinIO   │ │      │
│          │ │   / S3   │ │      │
└──────────┘ └──────────┘ └──────┘
```

---

## 📦 API Modules

### 1. [Authentication & Authorization](./api-docs/01-authentication-api.md)
- User registration and login
- OAuth integration (Google)
- JWT token management
- Password reset flow
- Session management

**Base Path:** `/api/v1/auth`

### 2. [User Management](./api-docs/02-user-management-api.md)
- User profile CRUD
- Child profiles management
- Address management

**Base Path:** `/api/v1/users`

### 3. [Book Templates](./api-docs/03-book-templates-api.md)
- Story book templates listing
- Coloring book templates listing
- Search and filtering
- Template details
- Template categories

**Base Path:** `/api/v1/templates`

### 4. [Book Generation](./api-docs/04-book-generation-api.md)
- Personalized book creation
- AI-powered story generation
- Image processing and integration
- Generation status tracking
- Preview generation

**Base Path:** `/api/v1/books/generate`

### 5. [Preview & Download](./api-docs/05-preview-download-api.md)
- Book preview access
- Full book download (after purchase)
- Preview page management
- Download tracking
- Email delivery

**Base Path:** `/api/v1/books`

### 6. [Orders & Checkout](./api-docs/06-orders-checkout-api.md)
- Cart management
- Order creation
- Order status tracking
- Order history
- Pricing calculation

**Base Path:** `/api/v1/orders`

### 7. [Payment Processing](./api-docs/07-payment-api.md)
- Payment intent creation
- Payment processing (Stripe integration)
- Payment status webhooks
- Refund handling
- Invoice generation

**Base Path:** `/api/v1/payments`

---

## 🛠 Technology Stack

### Core Framework
- **FastAPI** - High-performance async web framework
- **Pydantic** - Data validation and settings management
- **SQLAlchemy 2.0** - ORM with async support
- **Alembic** - Database migrations

### Database & Storage
- **PostgreSQL 15+** - Primary database
- **MinIO / AWS S3** - Book PDFs, images, and user uploads

### AI & Processing
- **OpenAI API** - Story generation
- **Pillow / PIL** - Image processing
- **Celery** - Background task processing
- **RabbitMQ** - Message broker for Celery (optional)

### Authentication & Security
- **python-jose** - JWT token handling
- **passlib** - Password hashing
- **python-multipart** - File upload handling
- **CORS middleware** - Cross-origin resource sharing

### Payment Processing
- **Stripe SDK** - Payment processing
- **stripe-python** - Official Stripe library

### Testing & Quality
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **httpx** - HTTP client for testing
- **faker** - Test data generation

---

## 🔄 Common Patterns

### Request/Response Structure

#### Standard Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2026-02-14T10:30:00Z"
}
```

#### Standard Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  },
  "timestamp": "2026-02-14T10:30:00Z"
}
```

#### Pagination Response
```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "totalPages": 5,
      "totalItems": 95,
      "hasNext": true,
      "hasPrev": false
    }
  }
}
```

---

## 🔐 Security & Authentication

### Authentication Flow

1. **User Login** → Server validates credentials → Returns JWT access token + refresh token
2. **Subsequent Requests** → Client sends `Authorization: Bearer <access_token>`
3. **Token Refresh** → When access token expires, use refresh token to get new access token
4. **OAuth Flow** → Redirect to OAuth provider → Callback → Create/link user → Return tokens

### Token Structure

**Access Token:**
- Expires in: 15 minutes
- Contains: user_id, email, role
- Used for: API authentication

**Refresh Token:**
- Expires in: 7 days
- Stored in: HTTP-only cookie (optional) or client storage
- Used for: Getting new access tokens

### Security Headers

All responses include:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

---

## ⚠️ Error Handling

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST (resource created) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource conflict (e.g., duplicate email) |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily down |

### Error Code Categories

- `AUTH_*` - Authentication errors
- `VALIDATION_*` - Input validation errors
- `RESOURCE_*` - Resource not found/conflicts
- `PAYMENT_*` - Payment processing errors
- `GENERATION_*` - Book generation errors
- `UPLOAD_*` - File upload errors

---

## 🔄 API Versioning

**Current Version:** v1

**URL Pattern:** `/api/v1/<resource>`

**Version Strategy:**
- Major version in URL path
- Breaking changes require new version
- Old versions supported for minimum 6 months
- Deprecation warnings in response headers

**Example:**
```
Current:  /api/v1/books
Future:   /api/v2/books (with breaking changes)
```

---

## 📊 Rate Limiting

### Default Limits (per user/IP)

| Endpoint Category | Rate Limit |
|------------------|------------|
| Authentication | 5 requests / minute |
| Read Operations | 100 requests / minute |
| Write Operations | 30 requests / minute |
| Book Generation | 5 requests / hour |
| File Uploads | 10 requests / hour |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1645789200
```

---

## 🔍 Monitoring & Logging

### Logging Levels

- **DEBUG** - Detailed information for debugging
- **INFO** - General informational messages
- **WARNING** - Warning messages
- **ERROR** - Error messages
- **CRITICAL** - Critical system errors

### Logged Information

- Request ID (for tracing)
- User ID (if authenticated)
- Endpoint accessed
- Response time
- Status code
- Error details (if any)

---

## 🧪 Testing Strategy

### Test Coverage Requirements

- **Unit Tests:** 80%+ coverage
- **Integration Tests:** Critical flows
- **API Tests:** All endpoints
- **Load Tests:** High-traffic scenarios

### Test Data

- Use factories for test data generation
- Separate test database
- Reset database state between tests

---

## 📚 Additional Resources

- [Database Schema](./schema/database-schema.md)
- [Environment Configuration](./config/environment-setup.md)
- [Deployment Guide](./deployment/deployment-guide.md)
- [API Client Examples](./examples/client-examples.md)

---

## 📝 Changelog

### Version 1.0 (February 14, 2026)
- Initial API design
- All core modules defined
- Authentication flow established
- Payment integration planned

---

## 👥 Contact & Support

**API Team:** api-team@storybloom.com  
**Documentation:** https://docs.storybloom.com/api  
**Support:** support@storybloom.com
