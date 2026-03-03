# Mock Generation Implementation Guide

## Overview

Mock generation functions have been implemented for all book generation APIs. These simulate the AI generation process and update MinIO storage and the database appropriately. When actual AI generation APIs are available, you can replace the mock implementation with real calls.

## What Was Implemented

### 1. Mock Generation Service (`app/services/mock_generation.py`)

This service simulates the entire book generation pipeline:

- **MockContentGenerator**: Creates mock images (cover, coloring pages) and PDFs
- **MockGenerationWorker**: Orchestrates the generation process with realistic timing and progress updates
- **start_mock_generation()**: Entry point that starts generation in the background

### 2. Updated Components

#### Repository (`app/repositories/generated_book.py`)
- Added `get_by_id_direct()`: Get generation without user filtering (for background workers)
- Added `update_fields()`: Update specific fields of a generation record

#### Service (`app/services/generated_book.py`)
- Integrated `start_mock_generation()` into all three generation methods:
  - `initiate_generation()` - Standard template-based generation
  - `initiate_photo_to_coloring_generation()` - Photo-to-coloring conversion
  - `initiate_theme_based_generation()` - AI theme-based generation

## How It Works

### Generation Flow

1. **User initiates generation** via API
2. **Record created** in database with status "queued"
3. **Mock worker starts** in background (async task)
4. **Progress updates**:
   - Status: queued → processing → completed
   - Progress: 0% → 100%
   - Steps updated in real-time
5. **Content generated**:
   - Cover image uploaded to MinIO
   - Preview pages (up to 5) uploaded to MinIO
   - Full PDF generated and uploaded to MinIO
6. **Database updated** with URLs and metadata
7. **Generation completed** - user can preview/download

### Generated Files

Mock files are uploaded to MinIO with this structure:
```
generated/{generation_id}/
├── cover.png
├── preview/
│   ├── page_1.png
│   ├── page_2.png
│   └── ...
└── {child_name}_book.pdf
```

### Timing Simulation

- **Photo-to-coloring**: ~10 seconds total
- **Theme-based**: ~15-20 seconds (varies by page count)
- **Standard generation**: ~15 seconds

The mock includes realistic delays between steps to simulate actual processing.

## API Endpoints

### 1. Initiate Generation

```http
POST /api/v1/books/generate
```
Standard template-based generation (story or coloring books).

### 2. Photo-to-Coloring

```http
POST /api/v1/books/generate/photo-to-coloring
```
Convert 1-10 photos directly to coloring pages.

### 3. Theme-Based Generation

```http
POST /api/v1/books/generate/theme-based
```
Generate AI coloring pages based on theme and reference photos (5-30 pages).

### 4. Check Status

```http
GET /api/v1/books/generate/{generation_id}/status
```
Get real-time generation status, progress, and step information.

### 5. Cancel Generation

```http
DELETE /api/v1/books/generate/{generation_id}
```
Cancel a queued or in-progress generation.

## Testing the Implementation

### Using Swagger UI

1. Navigate to: `http://localhost:8000/docs`
2. Find the "Book Generation" section
3. Try the "POST /api/v1/books/generate/photo-to-coloring" endpoint:
   - Upload 1-3 test images
   - Provide child information
   - Submit the request
4. Note the `generation_id` from the response
5. Poll the status endpoint to watch progress:
   ```
   GET /api/v1/books/generate/{generation_id}/status
   ```
6. Once completed, get the book details:
   ```
   GET /api/v1/books/{book_id}
   ```

### Using cURL

```bash
# Start generation
curl -X POST "http://localhost:8000/api/v1/books/generate/photo-to-coloring" \
  -F "child_name=Emma" \
  -F "child_age=5" \
  -F "child_gender=female" \
  -F "photos=@photo1.jpg" \
  -F "photos=@photo2.jpg"

# Check status
curl "http://localhost:8000/api/v1/books/generate/{generation_id}/status"
```

## Replacing with Real AI Generation

When your actual AI generation API is ready, follow these steps:

### Option 1: Replace Mock Functions Directly

1. Open `app/services/mock_generation.py`
2. Replace the mock content generation methods:
   - `generate_mock_cover_image()` → Call real AI image generation API
   - `generate_mock_coloring_page()` → Call real coloring page AI
   - `generate_mock_pdf()` → Call real PDF generation service
3. Update timing estimates based on actual API response times

### Option 2: Create Separate Service (Recommended)

1. Create `app/services/ai_generation.py`:
```python
"""Real AI Generation Service"""
from app.services.mock_generation import MockGenerationWorker

class AIGenerationWorker(MockGenerationWorker):
    """Real AI generation worker - extends mock worker"""
    
    async def _generate_coloring_page(self, ...):
        # Call actual AI API
        response = await openai_client.generate_image(...)
        return response.image_bytes
    
    async def _generate_pdf(self, ...):
        # Call actual PDF service
        pdf_bytes = await pdf_service.create_book(...)
        return pdf_bytes
```

2. Update `app/services/generated_book.py`:
```python
# Change import
from app.services.ai_generation import start_ai_generation

# Replace mock calls
await start_ai_generation(book.id, self.db)
```

### Option 3: Use Feature Flag

```python
from app.core.config import get_settings

settings = get_settings()

if settings.USE_MOCK_GENERATION:
    from app.services.mock_generation import start_mock_generation as start_generation
else:
    from app.services.ai_generation import start_ai_generation as start_generation

# Use unified interface
await start_generation(book.id, self.db)
```

## Database Schema

The `generated_books` table tracks all generation details:

- `status`: queued, processing, completed, failed, cancelled
- `progress`: 0-100%
- `current_step`: Current generation step name
- `generation_steps`: JSON object with step statuses
- `photos`: Array of uploaded photo URLs
- `cover_image_url`: Generated cover image URL
- `preview_pages`: JSON array of preview page objects
- `total_pages`: Total number of pages in the book

## MinIO Storage

All files are stored in the `pandatales` bucket with intelligent organization:

- **Uploaded photos**: `photos/{uuid}.{ext}`
- **Generated content**: `generated/{generation_id}/...`
- **Presigned URLs**: 7-day expiration for preview access

## Background Task Execution

Currently using `asyncio.create_task()` for background processing. For production, consider:

1. **Celery**: Distributed task queue with Redis/RabbitMQ
2. **AWS Lambda**: Serverless function execution
3. **Azure Functions**: Similar to Lambda
4. **RQ (Redis Queue)**: Simple Python job queue
5. **Kubernetes Jobs**: For containerized environments

Example Celery integration:
```python
# tasks.py
from celery import Celery

celery_app = Celery('pandatales')

@celery_app.task
def process_generation(generation_id: str):
    # Run generation
    worker = MockGenerationWorker(db)
    asyncio.run(worker.process_generation(UUID(generation_id)))

# In service:
process_generation.delay(str(book.id))
```

## Monitoring and Debugging

### Check Generation Status in Database

```sql
SELECT id, child_name, status, progress, current_step, created_at
FROM generated_books
WHERE status IN ('queued', 'processing')
ORDER BY created_at DESC;
```

### Check Generated Files in MinIO

1. Access MinIO console: `http://localhost:9001`
2. Navigate to `pandatales` bucket
3. Browse `generated/` folder

### View Logs

The mock generation service logs all steps:
```
INFO: starting_mock_generation generation_id=xxx
INFO: generation_status_updated status=processing progress=10
INFO: mock_generation_completed generation_id=xxx
```

## Error Handling

The mock generation includes comprehensive error handling:

- **Failed generations**: Marked with error_code and error_message
- **Automatic cleanup**: Failed files are tracked but not removed (for debugging)
- **Retry logic**: Not implemented in mock (add as needed)

## Performance Considerations

- **Concurrent generations**: Currently no limit on parallel generations
- **Resource usage**: Each generation creates background task
- **Memory**: Mock PDFs are small; real AI-generated PDFs may be larger
- **Storage**: Presigned URLs expire after 7 days

For production, implement:
- Queue-based processing with worker pools
- Rate limiting per user
- Storage quotas
- Automatic cleanup of old generations

## Next Steps

1. **Test the mock implementation** using Swagger UI
2. **Verify MinIO uploads** are working correctly
3. **Monitor database updates** during generation
4. **Prepare actual AI integration**:
   - OpenAI DALL-E for images
   - Custom PDF generation service
   - Image processing APIs
5. **Add background job queue** (Celery/RQ) for production
6. **Implement webhooks** for completion notifications
7. **Add generation analytics** and monitoring

## Support

For questions or issues:
- Check FastAPI logs for detailed error messages
- Verify MinIO is running and accessible
- Ensure database migrations are up to date
- Check that all dependencies are installed

---

**Last Updated**: March 1, 2026
**Status**: ✅ Mock implementation complete and ready for testing
