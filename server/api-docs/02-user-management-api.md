# User Management API

**Base Path:** `/api/v1/users`  
**Version:** 1.0  
**Authentication:** Required (JWT Bearer Token)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Endpoints](#endpoints)
3. [Data Models](#data-models)
4. [Error Codes](#error-codes)

---

## Overview

The User Management API handles user profiles, preferences, child profiles, and address management.

### Features
- User profile CRUD operations
- Child profile management (for personalized books)
- Address management (for physical book shipping)
- Account deletion

---

## Endpoints

### 1. Get User Profile

**Endpoint:** `GET /api/v1/users/profile`

**Description:** Get authenticated user's profile.

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
    "phone": "+1234567890",
    "avatar": "https://cdn.pandatales.com/avatars/usr_123.jpg",
    "emailVerified": true,
    "phoneVerified": false,
    "createdAt": "2026-01-15T10:30:00Z",
    "updatedAt": "2026-02-14T09:15:00Z"
  }
}
```

---

### 2. Update User Profile

**Endpoint:** `PATCH /api/v1/users/profile`

**Description:** Update user profile information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "firstName": "John",
  "lastName": "Smith",
  "phone": "+1234567890"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "id": "usr_1234567890",
    "email": "parent@example.com",
    "firstName": "John",
    "lastName": "Smith",
    "phone": "+1234567890",
    "updatedAt": "2026-02-14T10:30:00Z"
  }
}
```

---

### 3. Upload Avatar

**Endpoint:** `POST /api/v1/users/profile/avatar`

**Description:** Upload or update user avatar.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body:**
```
Form Data:
- avatar: <image_file> (max 5MB, jpg/png/webp)
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Avatar uploaded successfully",
  "data": {
    "avatarUrl": "https://cdn.pandatales.com/avatars/usr_123_1645678900.jpg"
  }
}
```

**Errors:**
- `400` - Invalid file format or size

---

### 4. List Child Profiles

**Endpoint:** `GET /api/v1/users/children`

**Description:** Get all child profiles for the user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "children": [
      {
        "id": "child_abc123",
        "name": "Emma",
        "age": 5,
        "gender": "female",
        "birthDate": "2021-03-15",
        "photo": "https://cdn.pandatales.com/children/child_abc123.jpg",
        "createdAt": "2026-01-20T10:30:00Z"
      },
      {
        "id": "child_def456",
        "name": "Oliver",
        "age": 7,
        "gender": "male",
        "birthDate": "2019-08-22",
        "photo": "https://cdn.pandatales.com/children/child_def456.jpg",
        "createdAt": "2026-01-25T14:20:00Z"
      }
    ],
    "totalCount": 2
  }
}
```

---

### 5. Create Child Profile

**Endpoint:** `POST /api/v1/users/children`

**Description:** Create a new child profile.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body:**
```
Form Data:
- name: string (required, 1-50 chars)
- age: integer (required, 0-18)
- gender: string (required, 'male'|'female'|'other')
- birthDate: string (optional, ISO date)
- photo: file (optional, max 10MB, jpg/png/webp)
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Child profile created successfully",
  "data": {
    "id": "child_abc123",
    "name": "Emma",
    "age": 5,
    "gender": "female",
    "birthDate": "2021-03-15",
    "photo": "https://cdn.pandatales.com/children/child_abc123.jpg",
    "createdAt": "2026-02-14T10:30:00Z"
  }
}
```

**Errors:**
- `400` - Invalid input data
- `403` - Maximum child profiles limit reached (e.g., 10)

---

### 6. Get Child Profile

**Endpoint:** `GET /api/v1/users/children/{childId}`

**Description:** Get details of a specific child profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `childId` - Child profile ID

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "child_abc123",
    "name": "Emma",
    "age": 5,
    "gender": "female",
    "birthDate": "2021-03-15",
    "photo": "https://cdn.pandatales.com/children/child_abc123.jpg",
    "booksCreated": 3,
    "createdAt": "2026-01-20T10:30:00Z",
    "updatedAt": "2026-02-10T15:20:00Z"
  }
}
```

**Errors:**
- `404` - Child profile not found
- `403` - Not authorized to access this child profile

---

### 7. Update Child Profile

**Endpoint:** `PATCH /api/v1/users/children/{childId}`

**Description:** Update child profile information.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Path Parameters:**
- `childId` - Child profile ID

**Request Body:**
```
Form Data (all optional):
- name: string
- age: integer
- gender: string
- birthDate: string
- photo: file
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Child profile updated successfully",
  "data": {
    "id": "child_abc123",
    "name": "Emma Rose",
    "age": 6,
    "gender": "female",
    "birthDate": "2021-03-15",
    "photo": "https://cdn.pandatales.com/children/child_abc123_new.jpg",
    "updatedAt": "2026-02-14T10:30:00Z"
  }
}
```

---

### 8. Delete Child Profile

**Endpoint:** `DELETE /api/v1/users/children/{childId}`

**Description:** Delete a child profile (soft delete).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `childId` - Child profile ID

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Child profile deleted successfully"
}
```

**Note:** Books created for this child will remain accessible.

---

### 9. List User Addresses

**Endpoint:** `GET /api/v1/users/addresses`

**Description:** Get all saved addresses for shipping.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "addresses": [
      {
        "id": "addr_123abc",
        "firstName": "John",
        "lastName": "Doe",
        "addressLine1": "123 Main Street",
        "addressLine2": "Apt 4B",
        "city": "New York",
        "state": "NY",
        "postalCode": "10001",
        "country": "US",
        "phone": "+1234567890",
        "isDefault": true,
        "createdAt": "2026-01-15T10:30:00Z"
      }
    ],
    "totalCount": 1
  }
}
```

---

### 10. Create Address

**Endpoint:** `POST /api/v1/users/addresses`

**Description:** Add a new shipping address.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "addressLine1": "123 Main Street",
  "addressLine2": "Apt 4B",
  "city": "New York",
  "state": "NY",
  "postalCode": "10001",
  "country": "US",
  "phone": "+1234567890",
  "isDefault": true
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Address added successfully",
  "data": {
    "id": "addr_123abc",
    "firstName": "John",
    "lastName": "Doe",
    "addressLine1": "123 Main Street",
    "addressLine2": "Apt 4B",
    "city": "New York",
    "state": "NY",
    "postalCode": "10001",
    "country": "US",
    "phone": "+1234567890",
    "isDefault": true,
    "createdAt": "2026-02-14T10:30:00Z"
  }
}
```

---

### 11. Update Address

**Endpoint:** `PATCH /api/v1/users/addresses/{addressId}`

**Description:** Update a shipping address.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `addressId` - Address ID

**Request Body:** (all fields optional)
```json
{
  "addressLine1": "456 Oak Avenue",
  "isDefault": true
}
```

**Response:** `200 OK`

---

### 12. Delete Address

**Endpoint:** `DELETE /api/v1/users/addresses/{addressId}`

**Description:** Delete a shipping address.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `addressId` - Address ID

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Address deleted successfully"
}
```

---

### 13. Delete Account

**Endpoint:** `DELETE /api/v1/users/account`

**Description:** Delete user account (requires password confirmation).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "password": "CurrentPassword123!",
  "confirmation": "DELETE MY ACCOUNT"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Account deletion initiated. You will receive a confirmation email."
}
```

---

## Data Models

### User Profile Model
```python
class UserProfile:
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    avatar: Optional[str]
    email_verified: bool
    phone_verified: bool
    created_at: datetime
    updated_at: datetime
```

### Child Profile Model
```python
class ChildProfile:
    id: str
    user_id: str
    name: str
    age: int
    gender: str  # 'male', 'female', 'other'
    birth_date: Optional[date]
    photo: Optional[str]
    books_created: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
```

### Address Model
```python
class Address:
    id: str
    user_id: str
    first_name: str
    last_name: str
    address_line1: str
    address_line2: Optional[str]
    city: str
    state: str
    postal_code: str
    country: str  # ISO 3166-1 alpha-2
    phone: str
    is_default: bool
    created_at: datetime
    updated_at: datetime
```

---

## Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `USER_NOT_FOUND` | 404 | User not found |
| `CHILD_NOT_FOUND` | 404 | Child profile not found |
| `ADDRESS_NOT_FOUND` | 404 | Address not found |
| `MAX_CHILDREN_LIMIT` | 403 | Maximum child profiles limit reached |
| `INVALID_FILE_FORMAT` | 400 | Unsupported image format |
| `FILE_TOO_LARGE` | 400 | File exceeds size limit |
| `UNAUTHORIZED_ACCESS` | 403 | Not authorized to access resource |

---

## Validation Rules

### Child Profile
- **Name:** 1-50 characters, letters and spaces only
- **Age:** 0-18 years
- **Gender:** 'male', 'female', or 'other'
- **Photo:** Max 10MB, jpg/png/webp format

### Address
- **Postal Code:** Format validation by country
- **Phone:** E.164 format recommended
- **Country:** ISO 3166-1 alpha-2 code

### Avatar
- **File Size:** Max 5MB
- **Format:** jpg, png, webp
- **Dimensions:** Min 100x100px, Max 2000x2000px

---

## Testing

### Test Cases

1. **Profile Management**
   - ✅ Get profile
   - ✅ Update profile
   - ✅ Upload avatar

2. **Child Profiles**
   - ✅ Create child profile
   - ✅ List children
   - ✅ Update child
   - ✅ Delete child
   - ✅ Maximum limit enforcement

3. **Address Management**
   - ✅ Add address
   - ✅ List addresses
   - ✅ Update address
   - ✅ Delete address
   - ✅ Default address handling

4. **Account Deletion**
   - ✅ Delete account flow
   - ✅ Grace period handling
