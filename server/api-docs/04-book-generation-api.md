# Book Generation API

**Base Path:** `/api/v1/books/generate`  
**Version:** 1.0  
**Authentication:** Required (JWT Bearer Token)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Generation Flow](#generation-flow)
3. [Endpoints](#endpoints)
4. [Data Models](#data-models)
5. [AI Integration](#ai-integration)
6. [Error Codes](#error-codes)

---

## Overview

The Book Generation API handles the creation of personalized books using AI-powered story generation and image processing.

### Features
- AI-powered story personalization
- Photo integration and processing
- Background task processing with Celery
- Real-time generation status updates
- Preview page generation
- PDF generation for download

---

## Generation Flow

```
┌──────┐                                    ┌──────┐
│Client│                                    │Server│
└──┬───┘                                    └──┬───┘
   │                                           │
   │ POST /books/generate                      │
   │ {templateId, childData, photos}           │
   ├──────────────────────────────────────────►│
   │                                           │
   │                                      [Queue Task]
   │                                           │
   │ ◄─────────────────────────────────────────┤
   │ {generationId, status: 'queued'}          │
   │                                           │
   │ GET /books/generate/{id}/status           │
   │ (polling every 2-3 seconds)               │
   ├──────────────────────────────────────────►│
   │                                           │
   │                                      [Processing]
   │                                       - AI Story
   │                                       - Image Processing
   │                                       - PDF Generation
   │                                           │
   │ ◄─────────────────────────────────────────┤
   │ {status: 'processing', progress: 45%}     │
   │                                           │
   │ GET /books/generate/{id}/status           │
   ├──────────────────────────────────────────►│
   │                                           │
   │ ◄─────────────────────────────────────────┤
   │ {status: 'completed', bookId}             │
   │                                           │
   │ Redirect to /preview/{bookId}             │
```

---

## Endpoints

### 1. Initiate Book Generation

**Endpoint:** `POST /api/v1/books/generate`

**Description:** Start the personalized book generation process.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body:**
```
Form Data:
- templateId: string (required)
- childId: string (optional, if using existing child profile)
- childName: string (required if no childId)
- childAge: integer (required if no childId)
- childGender: string (required if no childId, 'male'|'female'|'other')
- photos[]: file[] (required, 1-3 photos, max 10MB each)
- parentEmail: string (optional, for notifications)
```

**Response:** `202 Accepted`
```json
{
  "success": true,
  "message": "Book generation started",
  "data": {
    "generationId": "gen_abc123def456",
    "status": "queued",
    "estimatedTime": 180,
    "queuePosition": 3
  }
}
```

**Errors:**
- `400` - Invalid template ID or missing required fields
- `400` - Invalid photos (format, size, count)
- `403` - Generation limit exceeded
- `422` - Validation errors

---

### 2. Get Generation Status

**Endpoint:** `GET /api/v1/books/generate/{generationId}/status`

**Description:** Get current status of book generation.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `generationId` - Generation process ID

**Response:** `200 OK`

**Status: Queued**
```json
{
  "success": true,
  "data": {
    "generationId": "gen_abc123def456",
    "status": "queued",
    "queuePosition": 2,
    "estimatedWaitTime": 120,
    "createdAt": "2026-02-14T10:30:00Z"
  }
}
```

**Status: Processing**
```json
{
  "success": true,
  "data": {
    "generationId": "gen_abc123def456",
    "status": "processing",
    "progress": 45,
    "currentStep": "Generating story content",
    "steps": {
      "photoProcessing": "completed",
      "storyGeneration": "in_progress",
      "imageGeneration": "pending",
      "pdfGeneration": "pending"
    },
    "estimatedCompletionTime": 90
  }
}
```

**Status: Completed**
```json
{
  "success": true,
  "data": {
    "generationId": "gen_abc123def456",
    "status": "completed",
    "bookId": "book_xyz789",
    "progress": 100,
    "completedAt": "2026-02-14T10:35:00Z",
    "previewUrl": "/preview/book_xyz789"
  }
}
```

**Status: Failed**
```json
{
  "success": false,
  "data": {
    "generationId": "gen_abc123def456",
    "status": "failed",
    "error": {
      "code": "GENERATION_AI_ERROR",
      "message": "Failed to generate story content",
      "details": "AI service unavailable"
    },
    "failedAt": "2026-02-14T10:33:00Z"
  }
}
```

**Errors:**
- `404` - Generation ID not found
- `403` - Not authorized to access this generation

---

### 3. Cancel Generation

**Endpoint:** `DELETE /api/v1/books/generate/{generationId}`

**Description:** Cancel a queued or in-progress generation.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `generationId` - Generation process ID

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Generation cancelled successfully"
}
```

**Errors:**
- `400` - Generation already completed or failed
- `404` - Generation not found

---

### 4. List User's Generated Books

**Endpoint:** `GET /api/v1/books/generated`

**Description:** Get all books generated by the user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (integer, default: 1)
- `pageSize` (integer, default: 20)
- `childId` (string, optional): Filter by child
- `status` (string): Filter by status ('draft', 'preview', 'purchased')
- `sort` (string): Sort by ('newest', 'oldest', 'title')

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "book_xyz789",
        "templateId": "tmpl_sb_001",
        "templateTitle": "My First Adventure",
        "childName": "Emma",
        "childId": "child_abc123",
        "status": "preview",
        "coverImage": "https://cdn.storybloom.com/books/book_xyz789_cover.jpg",
        "isPurchased": false,
        "generatedAt": "2026-02-14T10:35:00Z",
        "previewUrl": "/preview/book_xyz789"
      },
      {
        "id": "book_abc456",
        "templateId": "tmpl_sb_002",
        "templateTitle": "The Magical Forest Quest",
        "childName": "Oliver",
        "childId": "child_def456",
        "status": "purchased",
        "coverImage": "https://cdn.storybloom.com/books/book_abc456_cover.jpg",
        "isPurchased": true,
        "purchasedAt": "2026-02-10T14:20:00Z",
        "generatedAt": "2026-02-10T11:15:00Z",
        "downloadUrl": "/books/book_abc456/download"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "totalPages": 1,
      "totalItems": 8,
      "hasNext": false,
      "hasPrev": false
    }
  }
}
```

---

### 5. Get Generated Book Details

**Endpoint:** `GET /api/v1/books/{bookId}`

**Description:** Get details of a specific generated book.

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
    "id": "book_xyz789",
    "templateId": "tmpl_sb_001",
    "template": {
      "title": "My First Adventure",
      "genre": "adventure",
      "ageGroup": "3-5"
    },
    "child": {
      "id": "child_abc123",
      "name": "Emma",
      "age": 5,
      "gender": "female"
    },
    "status": "preview",
    "isPurchased": false,
    "coverImage": "https://cdn.storybloom.com/books/book_xyz789_cover.jpg",
    "totalPages": 20,
    "previewPages": [
      {
        "pageNumber": 1,
        "imageUrl": "https://cdn.storybloom.com/books/book_xyz789_p1.jpg",
        "text": "Once upon a time, Emma went on an amazing adventure..."
      },
      {
        "pageNumber": 2,
        "imageUrl": "https://cdn.storybloom.com/books/book_xyz789_p2.jpg",
        "text": "Emma discovered a magical door..."
      }
    ],
    "generatedAt": "2026-02-14T10:35:00Z",
    "generationDuration": 158
  }
}
```

**Errors:**
- `404` - Book not found
- `403` - Not authorized to access this book

---

### 6. Delete Generated Book

**Endpoint:** `DELETE /api/v1/books/{bookId}`

**Description:** Delete a generated book (only unpurchased books).

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
  "message": "Book deleted successfully"
}
```

**Errors:**
- `403` - Cannot delete purchased books
- `404` - Book not found

---

### 7. Regenerate Book

**Endpoint:** `POST /api/v1/books/{bookId}/regenerate`

**Description:** Regenerate a book with the same parameters (useful if generation failed).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `bookId` - Original book ID

**Request Body:** (optional adjustments)
```json
{
  "photos": ["new_photo_1.jpg"]
}
```

**Response:** `202 Accepted`
```json
{
  "success": true,
  "message": "Book regeneration started",
  "data": {
    "generationId": "gen_new123",
    "status": "queued"
  }
}
```

---

### 8. Get Generation History

**Endpoint:** `GET /api/v1/books/generate/history`

**Description:** Get history of all generation attempts (including failed).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page`, `pageSize`
- `status`: 'completed', 'failed', 'cancelled'

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "generationId": "gen_abc123",
        "templateTitle": "My First Adventure",
        "childName": "Emma",
        "status": "completed",
        "bookId": "book_xyz789",
        "startedAt": "2026-02-14T10:30:00Z",
        "completedAt": "2026-02-14T10:35:00Z",
        "duration": 300
      },
      {
        "generationId": "gen_def456",
        "templateTitle": "Space Mission",
        "childName": "Oliver",
        "status": "failed",
        "error": "AI service timeout",
        "startedAt": "2026-02-13T15:20:00Z",
        "failedAt": "2026-02-13T15:25:00Z"
      }
    ],
    "pagination": {...}
  }
}
```

---

## Data Models

### Generation Request Model
```python
class GenerationRequest:
    id: str
    user_id: str
    template_id: str
    child_id: Optional[str]
    child_name: str
    child_age: int
    child_gender: str
    photos: List[str]  # S3 URLs
    status: str  # 'queued', 'processing', 'completed', 'failed', 'cancelled'
    progress: int  # 0-100
    current_step: Optional[str]
    book_id: Optional[str]
    error: Optional[dict]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_completion_time: Optional[int]  # seconds
```

### Generated Book Model
```python
class GeneratedBook:
    id: str
    user_id: str
    template_id: str
    child_id: Optional[str]
    child_name: str
    child_age: int
    child_gender: str
    status: str  # 'preview', 'purchased'
    is_purchased: bool
    cover_image: str
    total_pages: int
    preview_pages: List[dict]
    full_pdf_url: Optional[str]  # Only if purchased
    watermarked_pdf_url: str  # For preview
    generated_at: datetime
    generation_duration: int  # seconds
```

### Generation Step
```python
class GenerationStep:
    name: str
    status: str  # 'pending', 'in_progress', 'completed', 'failed'
    progress: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]
```

---

## AI Integration

### Story Generation Process

1. **Input Preparation**
   - Extract child data (name, age, gender)
   - Process photos (face detection, cropping)
   - Load template story structure
   - Apply customizations

2. **AI Prompt Construction**
```python
prompt = f"""
Create a personalized children's story based on:
- Template: {template.title}
- Child: {child_name}, age {child_age}, {child_gender}
- Genre: {template.genre}
- Age group: {template.age_group}

Story structure:
Page 1: [Introduction]
Page 2: [Challenge appears]
...
Page 20: [Resolution]

Make it engaging, age-appropriate, and include the child as the protagonist.
"""
```

3. **OpenAI API Call**
   - Model: GPT-4 or GPT-3.5-turbo
   - Temperature: 0.7
   - Max tokens: 2000
   - Response includes page-by-page content

4. **Image Processing**
   - Resize and optimize child photos
   - Face detection and alignment
   - Apply filters if needed
   - Generate character illustrations
   - Composite child's face onto character

5. **PDF Generation**
   - Combine text and images
   - Apply template layout
   - Generate full PDF
   - Generate watermarked preview PDF
   - Upload to S3

### Celery Task Structure

```python
@celery.task(bind=True)
def generate_book_task(self, generation_id: str):
    """
    Background task to generate personalized book
    """
    try:
        # Update status to processing
        update_generation_status(generation_id, "processing", 0)
        
        # Step 1: Process photos (25% progress)
        photos = process_photos(generation_id)
        update_generation_status(generation_id, "processing", 25)
        
        # Step 2: Generate story with AI (50% progress)
        story = generate_story_with_ai(generation_id)
        update_generation_status(generation_id, "processing", 50)
        
        # Step 3: Generate images (75% progress)
        images = generate_page_images(generation_id, story, photos)
        update_generation_status(generation_id, "processing", 75)
        
        # Step 4: Create PDFs (90% progress)
        pdf_urls = create_pdfs(generation_id, story, images)
        update_generation_status(generation_id, "processing", 90)
        
        # Step 5: Finalize (100% progress)
        book_id = save_generated_book(generation_id, pdf_urls)
        update_generation_status(generation_id, "completed", 100, book_id)
        
        # Send notification email
        send_completion_email(generation_id)
        
    except Exception as e:
        update_generation_status(generation_id, "failed", error=str(e))
        raise
```

---

## Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `GENERATION_INVALID_TEMPLATE` | 400 | Template not found or inactive |
| `GENERATION_INVALID_PHOTOS` | 400 | Invalid photo format, size, or count |
| `GENERATION_LIMIT_EXCEEDED` | 403 | Monthly generation limit reached |
| `GENERATION_AI_ERROR` | 500 | AI service error |
| `GENERATION_PROCESSING_ERROR` | 500 | Image processing error |
| `GENERATION_PDF_ERROR` | 500 | PDF generation error |
| `GENERATION_NOT_FOUND` | 404 | Generation ID not found |
| `GENERATION_ALREADY_COMPLETED` | 400 | Cannot cancel completed generation |

---

## Rate Limiting

- **Generation requests:** 5 per hour per user
- **Status checks:** 100 per minute per user
- **Monthly limit:** 20 generations per free user, unlimited for premium

---

## Testing

### Test Cases

1. **Generation Flow**
   - ✅ Valid generation request
   - ✅ Invalid template
   - ✅ Invalid photos
   - ✅ Status polling
   - ✅ Cancellation

2. **Photo Processing**
   - ✅ Valid formats (jpg, png, webp)
   - ✅ Size limits
   - ✅ face detection
   - ✅ Multiple photos

3. **AI Integration**
   - ✅ Story generation success
   - ✅ AI service timeout
   - ✅ AI service error handling

4. **PDF Generation**
   - ✅ Full PDF creation
   - ✅ Watermarked preview PDF
   - ✅ S3 upload

---

## Performance Considerations

### Optimization Strategies

1. **Queue Management**
   - Priority queue for premium users
   - Rate limiting per user tier
   - Celery worker scaling

2. **Caching**
   - Template data cached
   - AI prompts cached per template
   - Processed photos cached for regeneration

3. **Resource Management**
   - Image processing: Max 2048x2048px
   - PDF compression
   - S3 lifecycle policies for old generations

4. **Monitoring**
   - Average generation time
   - Failure rates by step
   - Queue length
   - AI API costs
