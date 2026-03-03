# MinIO Storage Integration - Error Handling Documentation

## Overview
This document describes the comprehensive error handling implementation for MinIO storage operations in the PandaTales API.

## Storage Service Implementation

### File: `app/services/storage.py`

The `StorageService` class provides a centralized interface for all MinIO operations with comprehensive error handling.

#### Key Features:
1. **Connection Validation**: Verifies MinIO connection and bucket existence on initialization
2. **Comprehensive Error Handling**: Catches and properly handles all MinIO S3Error types
3. **File Validation**: Validates file types, extensions, and sizes before upload
4. **Standardized Paths**: Follows the storage structure defined in MINIO_STORAGE_DESIGN.md
5. **Presigned URLs**: Generates secure, time-limited URLs for private content
6. **Public URL Support**: Direct URLs for public content (templates, marketing)

## Error Handling Strategy

### 1. MinIO Connection Errors
**Location**: `StorageService.__init__()`

**Handled Errors**:
- Connection failures to MinIO endpoint
- Invalid credentials (access key/secret key)
- Missing or inaccessible bucket

**Response**:
```python
raise InternalServerException(
    message="Failed to connect to storage service"
)
```

### 2. File Upload Errors
**Location**: `StorageService.upload_file()`

**Handled S3Error Codes**:
- `NoSuchBucket`: Storage bucket not found
- `AccessDenied`: Insufficient permissions
- `EntityTooLarge`: File exceeds storage system limits

**Validation Errors**:
- Empty file (0 bytes)
- File size exceeds max_size_mb parameter
- Invalid file content

**Logging**:
```python
logger.error(f"MinIO error uploading file '{object_name}': {e.code} - {e.message}")
```

### 3. Image Upload Errors
**Location**: `StorageService.upload_image()`

**Validation Checks**:
- Content type must start with "image/"
- File extension must be in allowed set (.jpg, .jpeg, .png, .webp)
- File size must be under specified limit (default 10MB)

**Example**:
```python
if not file.content_type or not file.content_type.startswith("image/"):
    raise BadRequestException(
        message=f"Invalid file type. Expected image, got: {file.content_type}"
    )
```

### 4. URL Generation Errors
**Location**: `StorageService.get_file_url()`

**Handled Errors**:
- `NoSuchKey`: File not found in storage
- URL generation failures
- Connection issues during stat_object check

**Response**:
```python
raise NotFoundException(
    message=f"File not found: {object_name}"
)
```

### 5. File Deletion Errors
**Location**: `StorageService.delete_file()`

**Handled Errors**:
- `NoSuchKey`: File doesn't exist (logged as warning, returns False)
- Other S3Errors: Logged and raised as InternalServerException

## API Endpoint Integration

### Updated Endpoints

#### 1. Book Generation (`/api/v1/books/generate`)
**File**: `app/api/v1/endpoints/generated_books.py`

**Upload Function**: `process_photo_uploads()`
- Uploads 1-3 photos to `users/uploads/photos/`
- Max 10MB per photo
- Returns list of object names (storage paths)

**Error Handling**:
```python
try:
    photo_urls = await process_photo_uploads(photos, storage_service)
except BadRequestException as e:
    return success_response(data=None, message=e.message, status_code=400)
except InternalServerException as e:
    logger.error(f"Storage error: {e.message}")
    return success_response(
        data=None,
        message="Failed to process photos. Please try again.",
        status_code=500
    )
```

#### 2. Photo-to-Coloring Generation (`/api/v1/books/generate/photo-to-coloring`)
**File**: `app/api/v1/endpoints/generated_books.py`

**Differences**:
- Accepts 1-10 photos instead of 1-3
- Same error handling pattern
- Same storage path (`users/uploads/photos/`)

#### 3. Theme-Based Generation (`/api/v1/books/generate/theme-based`)
**File**: `app/api/v1/endpoints/generated_books.py`

**Features**:
- Variable photo count based on theme config
- Same error handling and storage approach

#### 4. Avatar Upload (`/api/v1/users/profile/avatar`)
**File**: `app/api/v1/endpoints/users.py`

**Storage Path**: `users/avatars/{uuid}.{ext}`
**Max Size**: 5MB (per MAX_FILE_SIZE_AVATAR in config)

**Complete Implementation**:
```python
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    storage_service = StorageService()
    
    try:
        # Upload with validation
        object_name = await storage_service.upload_image(
            file=file,
            prefix="avatars",
            max_size_mb=5,
        )
        
        # Generate presigned URL
        avatar_url = await storage_service.get_file_url(object_name)
        
        # Update database
        service = UserService(db)
        await service.update_avatar(user_id, object_name)
        
        return success_response(
            data={"avatar_url": avatar_url},
            message="Avatar uploaded successfully"
        )
        
    except BadRequestException as e:
        logger.warning(f"Validation failed: {e.message}")
        return success_response(data=None, message=e.message, status_code=400)
        
    except InternalServerException as e:
        logger.error(f"Upload failed: {e.message}")
        return success_response(
            data=None,
            message="Failed to upload avatar. Please try again.",
            status_code=500
        )
```

## Exception Hierarchy

### Custom Exceptions
**File**: `app/common/exceptions.py`

```python
BadRequestException(message: str)
- Invalid file type
- File too large
- Invalid file extension
- Empty file

InternalServerException(message: str)
- MinIO connection failures
- Upload failures
- Access denied errors
- Bucket not found

NotFoundException(message: str)
- File not found during URL generation
- Object doesn't exist
```

## Logging Strategy

### Log Levels

#### INFO
- Successful uploads: `Successfully uploaded file: {object_name}`
- URL generation: `Generated presigned URL for: {object_name}`
- File deletion: `Deleted file: {object_name}`

#### WARNING
- File not found during deletion: `File not found for deletion: {object_name}`
- Validation failures: `Validation failed for user {user_id}: {message}`

#### ERROR
- All MinIO S3Errors with code and message
- Unexpected exceptions with full traceback
- Storage initialization failures

### Example Log Output
```
INFO: Uploading file to MinIO: users/avatars/123e4567-e89b-12d3-a456-426614174000.jpg (245760 bytes)
INFO: Successfully uploaded file: users/avatars/123e4567-e89b-12d3-a456-426614174000.jpg
INFO: Generated presigned URL for: users/avatars/123e4567-e89b-12d3-a456-426614174000.jpg

ERROR: MinIO error uploading file 'users/photos/invalid.jpg': AccessDenied - Access Denied
```

## Storage Path Structure

Per `MINIO_STORAGE_DESIGN.md`, files are organized as:

- `users/avatars/{uuid}.{ext}` - User profile pictures
- `users/uploads/photos/{uuid}.{ext}` - Child photos for book generation
- `templates/story-books/{covers|previews|samples}/{template_id}.{ext}` - Template assets
- `templates/coloring-books/{covers|previews|samples}/{template_id}.{ext}` - Template assets
- `generated/books/story/{pdfs|covers|pages}/{book_id}-{page}.{ext}` - Generated story books
- `generated/books/coloring/{pdfs|covers|pages}/{book_id}-{page}.{ext}` - Generated coloring books
- `generated/temp/{uuid}.{ext}` - Temporary files (auto-deleted after 7 days)
- `public/assets/*` - Public assets (CDN-cached)
- `public/marketing/*` - Marketing materials (CDN-cached)

## Testing Recommendations

### Unit Tests
1. Test all S3Error code branches
2. Test file validation (type, size, extension)
3. Test presigned URL generation
4. Test public URL generation

### Integration Tests
1. Test actual MinIO upload/download
2. Test error recovery
3. Test concurrent uploads
4. Test lifecycle policy (temp file deletion)

### Load Tests
1. Multiple simultaneous uploads
2. Large file uploads (near max size)
3. Presigned URL expiration behavior

## Security Considerations

1. **Presigned URLs**: Default 1-hour expiration for private content
2. **File Validation**: All uploads validated for type and size
3. **UUID Filenames**: Generated filenames prevent path traversal
4. **Access Control**: Bucket policies enforce public/private separation
5. **Error Messages**: Don't expose internal paths or system details to clients

## Future Enhancements

1. **Virus Scanning**: Integrate antivirus scanning before accepting uploads
2. **Image Processing**: Thumbnail generation, format conversion
3. **CDN Integration**: CloudFront or similar for public content
4. **Backup Strategy**: Replication to secondary storage
5. **Metrics**: Track upload success rates, sizes, and performance
6. **Rate Limiting**: Per-user upload quotas
7. **Retry Logic**: Automatic retry for transient MinIO failures
8. **Multipart Uploads**: Support for very large files (>100MB)

## Troubleshooting

### Common Issues

#### "Storage service is not properly configured"
- Bucket doesn't exist - run `scripts/init_minio.py`
- MinIO container not running - `docker-compose --profile minio up`

#### "Failed to connect to storage service"
- MinIO endpoint incorrect in `.env`
- Access key/secret key mismatch
- Network connectivity issue

#### "File size exceeds maximum allowed size"
- Client-side validation needed
- Check config.py MAX_FILE_SIZE_* settings
- Verify MINIO_STORAGE_DESIGN.md limits

#### "Invalid file type"
- Check allowed_extensions parameter
- Verify content_type is set correctly
- Some browsers may send incorrect MIME types

## Configuration

### Environment Variables
```env
STORAGE_PROVIDER=minio
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=pandatales
MINIO_SECURE=false
MINIO_REGION=us-east-1
```

### File Size Limits (config.py)
```python
MAX_FILE_SIZE_AVATAR: int = 5_242_880  # 5MB
MAX_FILE_SIZE_PHOTO: int = 10_485_760  # 10MB
MAX_FILE_SIZE_PDF: int = 52_428_800  # 50MB
```

## Summary

The MinIO storage integration provides:
- ✅ Comprehensive error handling for all S3Error types
- ✅ Built-in file validation (type, size, extension)
- ✅ Standardized storage paths per design document
- ✅ Secure presigned URLs for private content
- ✅ Detailed logging for debugging and monitoring
- ✅ Production-ready exception handling
- ✅ Type-safe implementation with proper async/await

All mutation APIs that interact with MinIO now have proper error handling and follow best practices for cloud storage operations.
