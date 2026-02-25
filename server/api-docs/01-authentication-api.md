# Authentication & Authorization API

**Base Path:** `/api/v1/auth`  
**Version:** 1.0

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication Flow](#authentication-flow)
3. [Endpoints](#endpoints)
4. [Data Models](#data-models)
5. [Error Codes](#error-codes)

---

## Overview

The Authentication API handles user registration, login, OAuth integration, and session management for Story Bloom.

### Features
- Email/password registration and login
- OAuth 2.0 integration (Google)
- JWT-based authentication
- Refresh token rotation
- Password reset flow
- Email verification

---

## Authentication Flow

### Standard Email/Password Flow

```
┌──────┐                                  ┌──────┐
│Client│                                  │Server│
└──┬───┘                                  └──┬───┘
   │                                         │
   │  POST /auth/register                    │
   ├────────────────────────────────────────►│
   │  {email, password, name}                │
   │                                         │
   │  ◄────────────────────────────────────┤
   │  {success, message}                     │
   │  (verification email sent)              │
   │                                         │
   │  POST /auth/verify-email                │
   ├────────────────────────────────────────►│
   │  {token}                                │
   │                                         │
   │  ◄────────────────────────────────────┤
   │  {success, tokens}                      │
   │                                         │
   │  POST /auth/login                       │
   ├────────────────────────────────────────►│
   │  {email, password}                      │
   │                                         │
   │  ◄────────────────────────────────────┤
   │  {accessToken, refreshToken, user}      │
```

### OAuth Flow (Google)

```
┌──────┐                    ┌──────┐                  ┌─────────┐
│Client│                    │Server│                  │ OAuth   │
│      │                    │      │                  │Provider │
└──┬───┘                    └──┬───┘                  └────┬────┘
   │                           │                           │
   │ GET /auth/oauth/google    │                           │
   ├──────────────────────────►│                           │
   │                           │                           │
   │ ◄─────────────────────────┤                           │
   │ {authUrl}                 │                           │
   │                           │                           │
   │ Redirect to authUrl       │                           │
   ├───────────────────────────┼──────────────────────────►│
   │                           │                           │
   │                           │  User authorizes          │
   │                           │                           │
   │ ◄─────────────────────────┼───────────────────────────┤
   │ Redirect to callback      │                           │
   │ with code                 │                           │
   │                           │                           │
   │ GET /auth/oauth/google/   │                           │
   │     callback?code=xxx     │                           │
   ├──────────────────────────►│                           │
   │                           │  Exchange code for token  │
   │                           ├──────────────────────────►│
   │                           │                           │
   │                           │ ◄─────────────────────────┤
   │                           │  User data                │
   │                           │                           │
   │ ◄─────────────────────────┤                           │
   │ {accessToken, refreshToken, user}                     │
```

---

## Endpoints

### 1. Register User

**Endpoint:** `POST /api/v1/auth/register`

**Description:** Register a new user with email and password.

**Request Body:**
```json
{
  "email": "parent@example.com",
  "password": "SecurePass123!",
  "firstName": "John",
  "lastName": "Doe",
  "phone": "+1234567890",
  "acceptedTerms": true
}
```

**Validation Rules:**
- `email`: Valid email format, unique in database
- `password`: Min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special char
- `firstName`: 1-50 chars, letters only
- `lastName`: 1-50 chars, letters only
- `phone`: Valid phone format (E.164 recommended)
- `acceptedTerms`: Must be `true`

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Registration successful. Please verify your email.",
  "data": {
    "userId": "usr_1234567890",
    "email": "parent@example.com",
    "emailVerificationSent": true
  }
}
```

**Errors:**
- `400` - Invalid input data
- `409` - Email already registered

---

### 2. Verify Email

**Endpoint:** `POST /api/v1/auth/verify-email`

**Description:** Verify user's email address with token sent via email.

**Request Body:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Email verified successfully",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "usr_1234567890",
      "email": "parent@example.com",
      "firstName": "John",
      "lastName": "Doe",
      "emailVerified": true,
      "createdAt": "2026-02-14T10:30:00Z"
    }
  }
}
```

**Errors:**
- `400` - Invalid or expired token
- `404` - User not found

---

### 3. Login

**Endpoint:** `POST /api/v1/auth/login`

**Description:** Login with email and password.

**Request Body:**
```json
{
  "email": "parent@example.com",
  "password": "SecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "tokenType": "Bearer",
    "expiresIn": 900,
    "user": {
      "id": "usr_1234567890",
      "email": "parent@example.com",
      "firstName": "John",
      "lastName": "Doe",
      "emailVerified": true,
      "role": "user"
    }
  }
}
```

**Errors:**
- `401` - Invalid credentials
- `403` - Email not verified
- `429` - Too many login attempts

---

### 4. Refresh Token

**Endpoint:** `POST /api/v1/auth/refresh`

**Description:** Get new access token using refresh token.

**Request Body:**
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "tokenType": "Bearer",
    "expiresIn": 900
  }
}
```

**Errors:**
- `401` - Invalid or expired refresh token

---

### 5. Logout

**Endpoint:** `POST /api/v1/auth/logout`

**Description:** Logout user and revoke tokens.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

### 6. Request Password Reset

**Endpoint:** `POST /api/v1/auth/forgot-password`

**Description:** Request password reset email.

**Request Body:**
```json
{
  "email": "parent@example.com"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "If the email exists, a password reset link has been sent"
}
```

**Note:** Always returns success to prevent email enumeration.

---

### 7. Reset Password

**Endpoint:** `POST /api/v1/auth/reset-password`

**Description:** Reset password with token from email.

**Request Body:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "newPassword": "NewSecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Password reset successfully"
}
```

**Errors:**
- `400` - Invalid or expired token
- `400` - Weak password

---

### 8. Change Password

**Endpoint:** `POST /api/v1/auth/change-password`

**Description:** Change password when logged in.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "currentPassword": "SecurePass123!",
  "newPassword": "NewSecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

**Errors:**
- `401` - Current password incorrect
- `400` - Weak new password

---

### 9. Get Current User

**Endpoint:** `GET /api/v1/auth/me`

**Description:** Get currently authenticated user details.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "usr_1234567890",
    "email": "parent@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "emailVerified": true,
    "role": "user",
    "createdAt": "2026-01-15T10:30:00Z",
    "lastLoginAt": "2026-02-14T09:15:00Z"
  }
}
```

**Errors:**
- `401` - Invalid or expired token

---

### 10. Initiate OAuth Login (Google)

**Endpoint:** `GET /api/v1/auth/oauth/google`

**Description:** Get Google OAuth authorization URL.

**Query Parameters:**
- `redirect_uri` (optional): Frontend callback URL

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "authUrl": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...&scope=...",
    "state": "random_state_token_123"
  }
}
```

---

### 11. OAuth Callback (Google)

**Endpoint:** `GET /api/v1/auth/oauth/google/callback`

**Description:** Handle OAuth callback from Google.

**Query Parameters:**
- `code`: Authorization code from Google
- `state`: State token for CSRF protection

**Response:** `302 Redirect`

Redirects to frontend with tokens:
```
https://storybloom.com/auth/callback?
  access_token=eyJhbG...&
  refresh_token=eyJhbG...&
  user_id=usr_123
```

Or error:
```
https://storybloom.com/auth/callback?error=access_denied
```

---

## Data Models

### User Model
```python
class User:
    id: str                    # usr_xxx format
    email: str
    password_hash: str         # bcrypt hashed
    first_name: str
    last_name: str
    phone: str
    email_verified: bool
    phone_verified: bool
    role: str                  # 'user', 'admin'
    oauth_provider: Optional[str]  # 'google', None
    oauth_provider_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
    is_active: bool
```

### Token Model
```python
class Token:
    access_token: str
    refresh_token: str
    token_type: str            # 'Bearer'
    expires_in: int            # seconds (900 = 15 min)
```

### JWT Payload (Access Token)
```python
{
    "sub": "usr_1234567890",   # user_id
    "email": "parent@example.com",
    "role": "user",
    "type": "access",
    "iat": 1645678900,         # issued at
    "exp": 1645679800          # expires at (15 min)
}
```

### JWT Payload (Refresh Token)
```python
{
    "sub": "usr_1234567890",
    "type": "refresh",
    "iat": 1645678900,
    "exp": 1646283700          # expires at (7 days)
}
```

---

## Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `AUTH_INVALID_CREDENTIALS` | 401 | Email or password incorrect |
| `AUTH_EMAIL_NOT_VERIFIED` | 403 | Email verification required |
| `AUTH_TOKEN_INVALID` | 401 | Invalid or malformed token |
| `AUTH_TOKEN_EXPIRED` | 401 | Token has expired |
| `AUTH_EMAIL_EXISTS` | 409 | Email already registered |
| `AUTH_WEAK_PASSWORD` | 400 | Password doesn't meet requirements |
| `AUTH_RATE_LIMIT` | 429 | Too many authentication attempts |
| `AUTH_OAUTH_FAILED` | 400 | OAuth authentication failed |
| `AUTH_INVALID_RESET_TOKEN` | 400 | Invalid password reset token |

---

## Security Considerations

### Password Requirements
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character (!@#$%^&*)

### Token Security
- Access tokens: Short-lived (15 minutes)
- Refresh tokens: Longer-lived (7 days)
- Refresh token rotation on use
- Token blacklisting on logout (can be implemented in database)
- Immediate revocation on logout

### Rate Limiting
- Login: 5 attempts per 15 minutes per IP
- Register: 3 attempts per hour per IP
- Password reset: 3 requests per hour per email
- Failed login lockout after 5 attempts for 30 minutes

### OAuth Security
- CSRF protection with state parameter
- PKCE flow for enhanced security
- Scope limitation to minimal required
- Verification of redirect URIs

---

## Testing

### Test Cases

1. **Registration**
   - ✅ Valid registration
   - ✅ Duplicate email
   - ✅ Weak password
   - ✅ Invalid email format

2. **Login**
   - ✅ Valid credentials
   - ✅ Invalid credentials
   - ✅ Unverified email
   - ✅ Rate limiting

3. **Token Management**
   - ✅ Token refresh
   - ✅ Expired token handling
   - ✅ Token revocation

4. **OAuth**
   - ✅ Google OAuth flow
   - ✅ Account linking
   - ✅ Error handling

---

## Implementation Notes

### Dependencies
```python
# requirements.txt
fastapi>=0.109.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
python-dotenv>=1.0.0
httpx>=0.26.0  # For OAuth
itsdangerous>=2.1.2  # For email tokens
```

### Environment Variables
```ini
# .env
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/oauth/google/callback

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@storybloom.com
SMTP_PASSWORD=xxx
```

---

## Next Steps

1. Implement user management endpoints (see [02-user-management-api.md](./02-user-management-api.md))
2. Set up email service for verification and password reset
3. Configure OAuth application with Google
4. Implement rate limiting middleware
5. Set up monitoring and logging for authentication events
