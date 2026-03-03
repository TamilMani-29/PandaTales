# Preview & Download API

**Base Path:** `/api/v1/books`  
**Version:** 1.0  
**Authentication:** Required (JWT Bearer Token)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Endpoints](#endpoints)
3. [Data Models](#data-models)
4. [Watermarking](#watermarking)

---

## Overview

The Preview & Download API provides access to view limited previews of generated books and download full books after purchase.

### Features
- Preview first 2 pages of generated books
- Watermarked preview PDF download
- Full book download for purchased books
- Download tracking and analytics
- Email delivery of purchased books
- Multiple format support (PDF, EPUB - future)

---

## Endpoints

### 1. Get Book Preview

**Endpoint:** `GET /api/v1/books/{bookId}/preview`

**Description:** Get preview pages of a generated book (first 2 pages).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `bookId` - Generated book ID

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "bookId": "book_xyz789",
    "title": "Emma's First Adventure",
    "childName": "Emma",
    "totalPages": 20,
    "previewPages": [
      {
        "pageNumber": 1,
        "imageUrl": "https://cdn.pandatales.com/books/book_xyz789_preview_p1.jpg",
        "thumbnailUrl": "https://cdn.pandatales.com/books/book_xyz789_preview_p1_thumb.jpg",
        "text": "Once upon a time, in a colorful world, lived a brave little hero named Emma...",
        "hasWatermark": true
      },
      {
        "pageNumber": 2,
        "imageUrl": "https://cdn.pandatales.com/books/book_xyz789_preview_p2.jpg",
        "thumbnailUrl": "https://cdn.pandatales.com/books/book_xyz789_preview_p2_thumb.jpg",
        "text": "One sunny morning, Emma discovered a mysterious map...",
        "hasWatermark": true
      }
    ],
    "lockedPages": [
      {
        "pageNumber": 3,
        "thumbnailUrl": "https://cdn.pandatales.com/books/book_xyz789_locked_p3_thumb.jpg",
        "isBlurred": true
      }
      // ... remaining pages (blurred thumbnails)
    ],
    "isPurchased": false,
    "pricing": {
      "digital": 19.99,
      "softcover": 29.99,
      "hardcover": 39.99
    }
  }
}
```

**Errors:**
- `404` - Book not found
- `403` - Not authorized to access this book

---

### 2. Get Preview PDF

**Endpoint:** `GET /api/v1/books/{bookId}/preview/pdf`

**Description:** Download watermarked preview PDF (first 2 pages).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `bookId` - Generated book ID

**Query Parameters:**
- `download` (boolean, default: false): Force download vs inline view

**Response:** `200 OK`
```
Content-Type: application/pdf
Content-Disposition: inline; filename="Emma-First-Adventure-Preview.pdf"
Content-Length: 1234567

[PDF Binary Data with watermarks]
```

**Features:**
- Watermarked with "PREVIEW - Unlock Full Book at pandatales.com"
- Only first 2 pages included
- Optimized file size
- Expires in 24 hours (signed URL)

**Errors:**
- `404` - Book not found
- `403` - Not authorized

---

### 3. Download Full Book (Purchased Only)

**Endpoint:** `GET /api/v1/books/{bookId}/download`

**Description:** Download full book PDF (only for purchased books).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `bookId` - Generated book ID

**Query Parameters:**
- `format` (string, default: 'pdf'): Download format ('pdf', 'epub')

**Response:** `200 OK`
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="Emma-First-Adventure.pdf"
Content-Length: 12345678

[Full PDF Binary Data - No Watermarks]
```

**Response Headers:**
```
X-Download-Id: dl_abc123
X-Download-Count: 5
X-Download-Limit: unlimited
```

**Errors:**
- `403` - Book not purchased
- `404` - Book not found

---

### 4. Get Download Link (Signed URL)

**Endpoint:** `POST /api/v1/books/{bookId}/download-link`

**Description:** Generate a temporary signed download link (expires in 1 hour).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `bookId` - Generated book ID

**Request Body:**
```json
{
  "format": "pdf",
  "expiresIn": 3600
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "downloadUrl": "https://cdn.pandatales.com/downloads/book_xyz789.pdf?token=eyJhbG...",
    "expiresAt": "2026-02-14T11:30:00Z",
    "expiresIn": 3600,
    "format": "pdf",
    "fileSize": 12345678,
    "fileName": "Emma-First-Adventure.pdf"
  }
}
```

**Use Case:** Email notifications with download links

**Errors:**
- `403` - Book not purchased

---

### 5. Get Book Pages (Purchased Only)

**Endpoint:** `GET /api/v1/books/{bookId}/pages`

**Description:** Get all pages of a purchased book (for in-app reading).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `bookId` - Generated book ID

**Query Parameters:**
- `page` (integer, optional): Specific page number
- `quality` (string, default: 'high'): Image quality ('low', 'medium', 'high')

**Response - All Pages:** `200 OK`
```json
{
  "success": true,
  "data": {
    "bookId": "book_xyz789",
    "title": "Emma's First Adventure",
    "totalPages": 20,
    "pages": [
      {
        "pageNumber": 1,
        "imageUrl": "https://cdn.pandatales.com/books/book_xyz789_full_p1_high.jpg",
        "thumbnailUrl": "https://cdn.pandatales.com/books/book_xyz789_full_p1_thumb.jpg",
        "text": "Once upon a time...",
        "hasWatermark": false
      }
      // ... all 20 pages
    ]
  }
}
```

**Response - Single Page:** `200 OK`
```json
{
  "success": true,
  "data": {
    "pageNumber": 5,
    "imageUrl": "https://cdn.pandatales.com/books/book_xyz789_full_p5_high.jpg",
    "text": "Emma continued her journey...",
    "nextPage": 6,
    "prevPage": 4
  }
}
```

**Errors:**
- `403` - Book not purchased
- `404` - Page not found

---

### 6. Track Download

**Endpoint:** `POST /api/v1/books/{bookId}/track-download`

**Description:** Record a download event (for analytics).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `bookId` - Generated book ID

**Request Body:**
```json
{
  "format": "pdf",
  "source": "dashboard",
  "device": "desktop"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Download tracked"
}
```

---

### 7. Get Download History

**Endpoint:** `GET /api/v1/books/{bookId}/downloads`

**Description:** Get download history for a specific book.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `bookId` - Generated book ID

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "bookId": "book_xyz789",
    "totalDownloads": 8,
    "downloads": [
      {
        "id": "dl_abc123",
        "format": "pdf",
        "downloadedAt": "2026-02-14T10:30:00Z",
        "device": "desktop",
        "ipAddress": "192.168.1.1",
        "userAgent": "Mozilla/5.0..."
      },
      {
        "id": "dl_def456",
        "format": "pdf",
        "downloadedAt": "2026-02-13T15:20:00Z",
        "device": "mobile",
        "ipAddress": "192.168.1.2"
      }
    ]
  }
}
```

---

## Data Models

### Book Page Model
```python
class BookPage:
    page_number: int
    image_url: str
    thumbnail_url: str
    text: str
    has_watermark: bool
    is_blurred: bool
```

### Download Record Model
```python
class DownloadRecord:
    id: str
    book_id: str
    user_id: str
    format: str  # 'pdf', 'epub'
    downloaded_at: datetime
    device: str
    ip_address: str
    user_agent: str
    file_size: int
```

---

## Watermarking

### Preview Watermark Specifications

**Text Watermark:**
- Content: "PREVIEW - Unlock at pandatales.com"
- Position: Diagonal across center
- Opacity: 15%
- Font: Arial, 48pt
- Color: Gray (#808080)

**Visual Watermark:**
- Panda Tales logo in corner
- Opacity: 20%
- Size: 100x100px
- Position: Bottom right

**PDF Watermark:**
- Applied to every preview page
- Cannot be removed easily
- Maintains readability

### Implementation
```python
def apply_watermark(image: Image, text: str) -> Image:
    """
    Apply watermark to preview image
    """
    watermark = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", 48)
    
    # Calculate watermark position (center, diagonal)
    width, height = image.size
    text_width, text_height = watermark.textsize(text, font)
    
    # Rotate and apply
    watermark.text(
        ((width - text_width) / 2, (height - text_height) / 2),
        text,
        font=font,
        fill=(128, 128, 128, 40)  # Gray with alpha
    )
    
    return image
```

---

## CDN & Storage

### S3 Bucket Structure
```
pandatales-books/
├── previews/
│   ├── book_xyz789_preview_p1.jpg
│   ├── book_xyz789_preview_p1_thumb.jpg
│   └── book_xyz789_preview.pdf
├── full/
│   ├── book_xyz789_full_p1.jpg
│   ├── book_xyz789_full_p1_thumb.jpg
│   └── book_xyz789_full.pdf
└── covers/
    └── book_xyz789_cover.jpg
```

### CloudFront Distribution

- **Preview Content:** Public read, 7-day cache
- **Full Content:** Requires signed URLs, 1-hour cache
- **Covers:** Public read, 30-day cache

### Signed URL Generation
```python
from botocore.signers import CloudFrontSigner

def generate_signed_download_url(
    book_id: str,
    expires_in: int = 3600
) -> str:
    """
    Generate CloudFront signed URL for secure downloads
    """
    url = f"https://cdn.pandatales.com/books/full/{book_id}_full.pdf"
    
    signer = CloudFrontSigner(KEY_ID, PRIVATE_KEY_LOADER)
    signed_url = signer.generate_presigned_url(
        url,
        date_less_than=datetime.now() + timedelta(seconds=expires_in)
    )
    
    return signed_url
```

---

## Performance Optimization

### Image Optimization

**Quality Levels:**
- **Thumbnail:** 400x300px, 70% quality, ~50KB
- **Medium:** 800x600px, 80% quality, ~200KB
- **High:** 1600x1200px, 90% quality, ~800KB

**Format:**
- WebP for web viewing (better compression)
- JPEG for PDF generation
- PNG for images with transparency

### Caching Strategy

- Preview pages: 24 hours cache
- Full pages: 1 hour cache (for purchased books)
- PDFs: Generate once, cache permanently
- Signed URLs: 1 hour expiry

---

## Analytics

### Tracked Metrics

1. **Preview Views**
   - Total preview views per book
   - Unique viewers
   - Time spent on preview
   - Pages viewed

2. **Downloads**
   - Total downloads per book
   - Downloads per format
   - Download success rate
   - Device breakdown


---

## Security

### Access Control

1. **Preview Access**
   - Owner must be authenticated
   - Book must belong to user
   - No limit on preview views

2. **Download Access**
   - Book must be purchased
   - User must be authenticated
   - Download link expires after 1 hour
   - Unlimited downloads after purchase

### DRM Considerations

- Watermarking (soft DRM)
- PDF encryption (optional)
- Download tracking
- Account sharing detection

---

## Testing

### Test Cases

1. **Preview Access**
   - ✅ View preview (owner)
   - ✅ Watermark presence
   - ✅ Locked pages blurred
   - ✅ Unauthorized access blocked

2. **Download**
   - ✅ Download purchased book
   - ✅ Download blocked for unpurchased
   - ✅ Format conversion
   - ✅ Signed URL expiry

3. **Analytics**
   - ✅ Track downloads
   - ✅ Track preview views
   - ✅ Download history
