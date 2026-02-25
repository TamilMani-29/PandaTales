# File Storage Optimization Guide

**For:** Story Bloom Backend  
**Storage:** MinIO / AWS S3  
**Date:** February 14, 2026

---

## 📋 Current vs Optimized Approach

### Current Implementation Issues

1. **❌ File uploads through FastAPI server** (multipart/form-data)
   - Increases server load and memory usage
   - Slower upload speeds
   - Scalability bottleneck

2. **❌ Missing file metadata tracking**
   - No file size, content type, or hash stored
   - Difficult to detect duplicates or corrupted files

3. **❌ No upload status/progress tracking**
   - Large files (10MB photos) have no progress indication

4. **❌ AWS-specific implementation**
   - CloudFront-specific signed URLs
   - Not directly compatible with MinIO

---

## ✅ Recommended Architecture

### 1. Direct Upload to S3/MinIO (Presigned URLs)

**Flow:**
```
┌──────┐                                   ┌──────┐                 ┌─────────┐
│Client│                                   │Server│                 │S3/MinIO │
└──┬───┘                                   └──┬───┘                 └────┬────┘
   │                                          │                          │
   │ 1. Request upload permission             │                          │
   │ POST /upload/presigned-url               │                          │
   ├─────────────────────────────────────────►│                          │
   │                                          │                          │
   │ 2. Generate presigned URL                │ 3. Generate presigned    │
   │                                          ├─────────────────────────►│
   │                                          │                          │
   │ ◄────────────────────────────────────────┤ ◄────────────────────────┤
   │ {uploadUrl, fields, fileId}              │                          │
   │                                          │                          │
   │ 4. Direct upload to S3/MinIO             │                          │
   ├──────────────────────────────────────────────────────────────────►│
   │ PUT {file}                               │                          │
   │                                          │                          │
   │ ◄──────────────────────────────────────────────────────────────────┤
   │ 200 OK                                   │                          │
   │                                          │                          │
   │ 5. Confirm upload completion             │                          │
   │ POST /upload/confirm                     │                          │
   ├─────────────────────────────────────────►│ 6. Verify file exists    │
   │                                          ├─────────────────────────►│
   │                                          │                          │
   │ ◄────────────────────────────────────────┤                          │
   │ {success: true, url}                     │                          │
```

---

## 🗄️ Database Schema Updates

### New Table: `file_uploads`

**Purpose:** Track all file uploads with metadata

```sql
CREATE TABLE file_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- File info
    file_key VARCHAR(500) NOT NULL,  -- S3/MinIO object key
    file_name VARCHAR(255) NOT NULL,  -- Original filename
    file_size BIGINT NOT NULL,  -- Size in bytes
    content_type VARCHAR(100) NOT NULL,  -- MIME type
    file_hash VARCHAR(64),  -- SHA-256 hash for deduplication
    
    -- Storage details
    bucket_name VARCHAR(100) NOT NULL,
    storage_provider VARCHAR(20) DEFAULT 's3' CHECK (storage_provider IN ('s3', 'minio')),
    
    -- URLs
    presigned_upload_url TEXT,  -- Temporary upload URL
    public_url VARCHAR(500),  -- Permanent URL (if public)
    cdn_url VARCHAR(500),  -- CDN URL (CloudFront/MinIO)
    
    -- Purpose
    purpose VARCHAR(50) NOT NULL CHECK (purpose IN (
        'user_avatar', 'child_photo', 'book_cover', 'book_page', 
        'book_pdf', 'template_image', 'other'
    )),
    
    -- Upload status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN (
        'pending', 'uploading', 'completed', 'failed', 'deleted'
    )),
    upload_started_at TIMESTAMP WITH TIME ZONE,
    upload_completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Reference to related entity
    related_entity_type VARCHAR(50),  -- 'book', 'user', 'child_profile', etc.
    related_entity_id UUID,
    
    -- Error tracking
    error_message TEXT,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_file_uploads_user_id ON file_uploads(user_id);
CREATE INDEX idx_file_uploads_file_key ON file_uploads(file_key);
CREATE INDEX idx_file_uploads_file_hash ON file_uploads(file_hash);
CREATE INDEX idx_file_uploads_status ON file_uploads(status);
CREATE INDEX idx_file_uploads_purpose ON file_uploads(purpose);
CREATE INDEX idx_file_uploads_related ON file_uploads(related_entity_type, related_entity_id);
CREATE INDEX idx_file_uploads_created ON file_uploads(created_at DESC);

-- Unique constraint for file hash (deduplication)
CREATE UNIQUE INDEX idx_file_uploads_hash_unique 
    ON file_uploads(file_hash) 
    WHERE file_hash IS NOT NULL AND is_deleted = FALSE;

COMMENT ON TABLE file_uploads IS 'Track all file uploads with metadata and status';
COMMENT ON COLUMN file_uploads.file_hash IS 'SHA-256 hash for deduplication';
COMMENT ON COLUMN file_uploads.file_key IS 'S3/MinIO object key (e.g., uploads/photos/abc123.jpg)';
```

### Update Existing Tables

Add file_upload_id references to existing tables:

```sql
-- Child profiles
ALTER TABLE child_profiles 
    ADD COLUMN photo_upload_id UUID REFERENCES file_uploads(id);

-- Generated books
ALTER TABLE generated_books 
    ADD COLUMN cover_upload_id UUID REFERENCES file_uploads(id),
    ADD COLUMN watermarked_pdf_upload_id UUID REFERENCES file_uploads(id),
    ADD COLUMN full_pdf_upload_id UUID REFERENCES file_uploads(id);

-- Book pages
ALTER TABLE book_pages 
    ADD COLUMN image_upload_id UUID REFERENCES file_uploads(id),
    ADD COLUMN thumbnail_upload_id UUID REFERENCES file_uploads(id);

-- Book templates
ALTER TABLE book_templates 
    ADD COLUMN cover_upload_id UUID REFERENCES file_uploads(id);
```

---

## 🚀 API Endpoints for Optimized Upload

### New Endpoints in File Upload API

Create new file: `server/api-docs/08-file-upload-api.md`

```markdown
# File Upload API

**Base Path:** `/api/v1/uploads`  
**Version:** 1.0  
**Authentication:** Required (JWT Bearer Token)

---

## Endpoints

### 1. Request Presigned Upload URL

**Endpoint:** `POST /api/v1/uploads/presigned-url`

**Description:** Get a presigned URL for direct upload to S3/MinIO.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "fileName": "child_photo.jpg",
  "fileSize": 2048576,
  "contentType": "image/jpeg",
  "purpose": "child_photo",
  "relatedEntityType": "child_profile",
  "relatedEntityId": "uuid-here"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "uploadId": "upload_abc123",
    "uploadUrl": "https://s3.amazonaws.com/bucket/key?signature=...",
    "fields": {
      "key": "uploads/photos/child_photo_abc123.jpg",
      "x-amz-algorithm": "AWS4-HMAC-SHA256",
      "x-amz-credential": "...",
      "x-amz-date": "...",
      "policy": "...",
      "x-amz-signature": "..."
    },
    "method": "POST",
    "expiresAt": "2026-02-14T11:00:00Z",
    "maxFileSize": 10485760
  }
}
```

**For MinIO:**
```json
{
  "success": true,
  "data": {
    "uploadId": "upload_abc123",
    "uploadUrl": "https://minio.yourdomain.com/bucket/uploads/photos/child_photo_abc123.jpg?X-Amz-Algorithm=...",
    "method": "PUT",
    "headers": {
      "Content-Type": "image/jpeg"
    },
    "expiresAt": "2026-02-14T11:00:00Z"
  }
}
```

---

### 2. Confirm Upload Completion

**Endpoint:** `POST /api/v1/uploads/{uploadId}/confirm`

**Description:** Confirm that file upload is complete and validate file.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `uploadId` - Upload tracking ID

**Request Body:**
```json
{
  "etag": "d41d8cd98f00b204e9800998ecf8427e",
  "fileHash": "sha256_hash_of_file"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Upload confirmed successfully",
  "data": {
    "fileId": "upload_abc123",
    "url": "https://storybloom-bucket.s3.amazonaws.com/uploads/photos/child_photo_abc123.jpg",
    "cdnUrl": "https://cdn.storybloom.com/uploads/photos/child_photo_abc123.jpg",
    "fileSize": 2048576,
    "contentType": "image/jpeg"
  }
}
```

**Errors:**
- `404` - Upload ID not found
- `400` - File not found in storage
- `400` - File validation failed (size, type, hash mismatch)

---

### 3. Get Upload Status

**Endpoint:** `GET /api/v1/uploads/{uploadId}/status`

**Description:** Check status of a file upload.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "uploadId": "upload_abc123",
    "status": "completed",
    "fileName": "child_photo.jpg",
    "fileSize": 2048576,
    "purpose": "child_photo",
    "url": "https://cdn.storybloom.com/...",
    "createdAt": "2026-02-14T10:30:00Z",
    "completedAt": "2026-02-14T10:30:45Z"
  }
}
```

---

### 4. Delete Uploaded File

**Endpoint:** `DELETE /api/v1/uploads/{uploadId}`

**Description:** Soft delete an uploaded file.

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "File marked for deletion"
}
```

---

### 5. List User Uploads

**Endpoint:** `GET /api/v1/uploads`

**Description:** Get list of user's uploaded files.

**Query Parameters:**
- `purpose` (optional): Filter by purpose
- `status` (optional): Filter by status
- `page` (default: 1)
- `limit` (default: 20)

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "uploads": [
      {
        "uploadId": "upload_abc123",
        "fileName": "child_photo.jpg",
        "fileSize": 2048576,
        "purpose": "child_photo",
        "status": "completed",
        "url": "https://cdn.storybloom.com/...",
        "createdAt": "2026-02-14T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "pages": 3
    }
  }
}
```
```

---

## 💻 Implementation Code

### Python Backend (FastAPI)

**File: `app/services/storage_service.py`**

```python
from typing import Literal, Optional
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import hashlib
from datetime import datetime, timedelta
import uuid

class StorageService:
    """
    Unified storage service supporting both AWS S3 and MinIO
    """
    
    def __init__(
        self,
        provider: Literal["s3", "minio"] = "s3",
        bucket_name: str = None,
        endpoint_url: Optional[str] = None,
        access_key: str = None,
        secret_key: str = None,
        region: str = "us-east-1"
    ):
        self.provider = provider
        self.bucket_name = bucket_name
        
        # Configure client
        config = Config(
            signature_version='s3v4',
            region_name=region
        )
        
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,  # For MinIO: http://minio:9000
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=config
        )
    
    def generate_presigned_upload_url(
        self,
        file_key: str,
        content_type: str,
        expires_in: int = 3600,
        max_file_size: int = 10485760  # 10MB
    ) -> dict:
        """
        Generate presigned URL for direct upload
        
        Returns:
            For S3: POST with form fields
            For MinIO: PUT with headers
        """
        try:
            if self.provider == "minio":
                # MinIO: Use PUT method
                url = self.s3_client.generate_presigned_url(
                    'put_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': file_key,
                        'ContentType': content_type
                    },
                    ExpiresIn=expires_in
                )
                
                return {
                    'url': url,
                    'method': 'PUT',
                    'headers': {
                        'Content-Type': content_type
                    }
                }
            else:
                # AWS S3: Use POST with policy
                conditions = [
                    {'bucket': self.bucket_name},
                    ['starts-with', '$key', file_key.rsplit('/', 1)[0] + '/'],
                    {'Content-Type': content_type},
                    ['content-length-range', 0, max_file_size]
                ]
                
                post = self.s3_client.generate_presigned_post(
                    Bucket=self.bucket_name,
                    Key=file_key,
                    Fields={'Content-Type': content_type},
                    Conditions=conditions,
                    ExpiresIn=expires_in
                )
                
                return {
                    'url': post['url'],
                    'method': 'POST',
                    'fields': post['fields']
                }
        
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")
    
    def verify_file_exists(
        self,
        file_key: str
    ) -> bool:
        """
        Verify that file exists in storage
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            return True
        except ClientError:
            return False
    
    def get_file_metadata(
        self,
        file_key: str
    ) -> dict:
        """
        Get file metadata from storage
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            
            return {
                'size': response['ContentLength'],
                'content_type': response['ContentType'],
                'etag': response['ETag'].strip('"'),
                'last_modified': response['LastModified']
            }
        except ClientError as e:
            raise Exception(f"Failed to get file metadata: {str(e)}")
    
    def generate_presigned_download_url(
        self,
        file_key: str,
        expires_in: int = 3600,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate presigned URL for secure download
        """
        params = {
            'Bucket': self.bucket_name,
            'Key': file_key
        }
        
        if filename:
            params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            raise Exception(f"Failed to generate download URL: {str(e)}")
    
    def delete_file(
        self,
        file_key: str
    ) -> bool:
        """
        Delete file from storage
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            return True
        except ClientError as e:
            raise Exception(f"Failed to delete file: {str(e)}")
    
    def generate_file_key(
        self,
        purpose: str,
        filename: str,
        user_id: str
    ) -> str:
        """
        Generate organized file key/path
        """
        # Extract extension
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        # Generate unique ID
        unique_id = str(uuid.uuid4())[:12]
        
        # Purpose-based folder structure
        folder_map = {
            'user_avatar': 'avatars',
            'child_photo': 'photos/children',
            'book_cover': 'books/covers',
            'book_page': 'books/pages',
            'book_pdf': 'books/pdfs',
            'template_image': 'templates/images'
        }
        
        folder = folder_map.get(purpose, 'uploads')
        
        # Format: folder/user_id/unique_id.ext
        return f"{folder}/{user_id}/{unique_id}.{ext}"
    
    def calculate_file_hash(
        self,
        file_key: str
    ) -> str:
        """
        Calculate SHA-256 hash of file in storage
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            
            sha256 = hashlib.sha256()
            for chunk in response['Body'].iter_chunks(chunk_size=8192):
                sha256.update(chunk)
            
            return sha256.hexdigest()
        except ClientError as e:
            raise Exception(f"Failed to calculate hash: {str(e)}")


# Usage example
def get_storage_service() -> StorageService:
    """
    Factory function to get storage service based on config
    """
    from app.core.config import settings
    
    if settings.STORAGE_PROVIDER == "minio":
        return StorageService(
            provider="minio",
            bucket_name=settings.MINIO_BUCKET,
            endpoint_url=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY
        )
    else:
        return StorageService(
            provider="s3",
            bucket_name=settings.S3_BUCKET,
            access_key=settings.AWS_ACCESS_KEY_ID,
            secret_key=settings.AWS_SECRET_ACCESS_KEY,
            region=settings.AWS_REGION
        )
```

**File: `app/api/v1/endpoints/uploads.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.storage_service import get_storage_service
from app.db.session import get_db
from app.models.file_upload import FileUpload
from app.core.security import get_current_user
from pydantic import BaseModel
from typing import Literal

router = APIRouter()

class PresignedURLRequest(BaseModel):
    fileName: str
    fileSize: int
    contentType: str
    purpose: Literal[
        'user_avatar', 'child_photo', 'book_cover', 
        'book_page', 'book_pdf', 'template_image'
    ]
    relatedEntityType: str = None
    relatedEntityId: str = None

class UploadConfirmRequest(BaseModel):
    etag: str = None
    fileHash: str = None

@router.post("/presigned-url")
async def request_presigned_upload_url(
    request: PresignedURLRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate presigned URL for direct upload to S3/MinIO
    """
    storage = get_storage_service()
    
    # Validate file size (max 10MB for photos)
    max_sizes = {
        'user_avatar': 5 * 1024 * 1024,  # 5MB
        'child_photo': 10 * 1024 * 1024,  # 10MB
        'book_cover': 5 * 1024 * 1024,
        'book_page': 5 * 1024 * 1024,
        'book_pdf': 50 * 1024 * 1024,  # 50MB
        'template_image': 10 * 1024 * 1024
    }
    
    if request.fileSize > max_sizes.get(request.purpose, 10 * 1024 * 1024):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum allowed"
        )
    
    # Generate file key
    file_key = storage.generate_file_key(
        purpose=request.purpose,
        filename=request.fileName,
        user_id=str(current_user.id)
    )
    
    # Create upload record
    upload = FileUpload(
        user_id=current_user.id,
        file_key=file_key,
        file_name=request.fileName,
        file_size=request.fileSize,
        content_type=request.contentType,
        bucket_name=storage.bucket_name,
        storage_provider=storage.provider,
        purpose=request.purpose,
        status='pending',
        related_entity_type=request.relatedEntityType,
        related_entity_id=request.relatedEntityId
    )
    
    db.add(upload)
    await db.commit()
    await db.refresh(upload)
    
    # Generate presigned URL
    presigned_data = storage.generate_presigned_upload_url(
        file_key=file_key,
        content_type=request.contentType,
        max_file_size=max_sizes.get(request.purpose, 10 * 1024 * 1024)
    )
    
    return {
        "success": True,
        "data": {
            "uploadId": str(upload.id),
            "uploadUrl": presigned_data['url'],
            "method": presigned_data['method'],
            **({'fields': presigned_data['fields']} if 'fields' in presigned_data else {}),
            **({'headers': presigned_data['headers']} if 'headers' in presigned_data else {}),
            "expiresAt": upload.created_at + timedelta(hours=1),
            "maxFileSize": max_sizes.get(request.purpose, 10 * 1024 * 1024)
        }
    }

@router.post("/{upload_id}/confirm")
async def confirm_upload(
    upload_id: str,
    request: UploadConfirmRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm upload completion and validate file
    """
    # Get upload record
    upload = await db.get(FileUpload, upload_id)
    
    if not upload or upload.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    storage = get_storage_service()
    
    # Verify file exists
    if not storage.verify_file_exists(upload.file_key):
        upload.status = 'failed'
        upload.error_message = "File not found in storage"
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File not found in storage"
        )
    
    # Get file metadata
    metadata = storage.get_file_metadata(upload.file_key)
    
    # Validate file size
    if abs(metadata['size'] - upload.file_size) > 1024:  # Allow 1KB variance
        upload.status = 'failed'
        upload.error_message = "File size mismatch"
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size validation failed"
        )
    
    # Calculate and store file hash
    file_hash = storage.calculate_file_hash(upload.file_key)
    upload.file_hash = file_hash
    
    # Update upload record
    upload.status = 'completed'
    upload.upload_completed_at = datetime.utcnow()
    upload.file_size = metadata['size']  # Update with actual size
    
    # Generate public/CDN URL
    if storage.provider == "minio":
        upload.public_url = f"{storage.endpoint_url}/{storage.bucket_name}/{upload.file_key}"
    else:
        upload.public_url = f"https://{storage.bucket_name}.s3.amazonaws.com/{upload.file_key}"
    
    await db.commit()
    await db.refresh(upload)
    
    return {
        "success": True,
        "message": "Upload confirmed successfully",
        "data": {
            "fileId": str(upload.id),
            "url": upload.public_url,
            "cdnUrl": upload.cdn_url or upload.public_url,
            "fileSize": upload.file_size,
            "contentType": upload.content_type,
            "fileHash": upload.file_hash
        }
    }
```

---

## 🔧 Configuration

### Environment Variables

```env
# Storage Provider ('s3' or 'minio')
STORAGE_PROVIDER=minio

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET=storybloom-files

# MinIO Configuration
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=storybloom-files
MINIO_SECURE=false  # Use HTTPS

# CloudFront (optional, for S3)
CLOUDFRONT_DOMAIN=cdn.storybloom.com
CLOUDFRONT_KEY_ID=your-key-id
CLOUDFRONT_PRIVATE_KEY_PATH=/path/to/private-key.pem

# File Upload Limits
MAX_FILE_SIZE_AVATAR=5242880  # 5MB
MAX_FILE_SIZE_PHOTO=10485760  # 10MB
MAX_FILE_SIZE_PDF=52428800    # 50MB

# Presigned URL Expiry (seconds)
PRESIGNED_URL_EXPIRY=3600  # 1 hour
```

---

## 🧪 Client Implementation

### TypeScript/React Example

```typescript
// Upload service
export class FileUploadService {
  private apiUrl = process.env.NEXT_PUBLIC_API_URL;

  async uploadFile(
    file: File,
    purpose: string,
    onProgress?: (progress: number) => void
  ): Promise<UploadResult> {
    // Step 1: Request presigned URL
    const presignedResponse = await fetch(`${this.apiUrl}/uploads/presigned-url`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAccessToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        fileName: file.name,
        fileSize: file.size,
        contentType: file.type,
        purpose
      })
    });

    const { data } = await presignedResponse.json();
    
    // Step 2: Upload directly to S3/MinIO
    let uploadResponse;
    
    if (data.method === 'PUT') {
      // MinIO PUT method
      uploadResponse = await fetch(data.uploadUrl, {
        method: 'PUT',
        headers: data.headers,
        body: file,
        onUploadProgress: (e) => {
          if (onProgress && e.total) {
            onProgress((e.loaded / e.total) * 100);
          }
        }
      });
    } else {
      // S3 POST method with form data
      const formData = new FormData();
      Object.entries(data.fields).forEach(([key, value]) => {
        formData.append(key, value as string);
      });
      formData.append('file', file);

      uploadResponse = await fetch(data.uploadUrl, {
        method: 'POST',
        body: formData,
        onUploadProgress: (e) => {
          if (onProgress && e.total) {
            onProgress((e.loaded / e.total) * 100);
          }
        }
      });
    }

    if (!uploadResponse.ok) {
      throw new Error('Upload failed');
    }

    // Step 3: Confirm upload
    const etag = uploadResponse.headers.get('ETag');
    const confirmResponse = await fetch(
      `${this.apiUrl}/uploads/${data.uploadId}/confirm`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAccessToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ etag })
      }
    );

    const result = await confirmResponse.json();
    return result.data;
  }
}

// Usage in component
const handleFileUpload = async (file: File) => {
  const uploadService = new FileUploadService();
  
  try {
    const result = await uploadService.uploadFile(
      file,
      'child_photo',
      (progress) => {
        setUploadProgress(progress);
      }
    );
    
    console.log('Upload successful:', result.url);
  } catch (error) {
    console.error('Upload failed:', error);
  }
};
```

---

## 📊 Benefits Summary

| Aspect | Before (Multipart) | After (Presigned URLs) |
|--------|-------------------|------------------------|
| **Upload Speed** | Slow (through server) | Fast (direct to storage) |
| **Server Load** | High (processes files) | Low (only generates URLs) |
| **Scalability** | Limited | Excellent |
| **Bandwidth** | 2x (client→server→storage) | 1x (client→storage) |
| **Progress Tracking** | Difficult | Native XHR support |
| **Large File Support** | Memory intensive | Efficient |
| **Cost** | Higher (server bandwidth) | Lower (direct to storage) |

---

## 🔐 Security Considerations

1. **Presigned URL Expiry**: Keep short (1 hour) to prevent abuse
2. **File Size Validation**: Enforce on both client and server
3. **Content Type Validation**: Verify MIME types
4. **Hash Verification**: Detect corrupted or tampered files
5. **Access Control**: Only file owner can access presigned URLs
6. **Rate Limiting**: Prevent upload spam
7. **Virus Scanning**: Integrate ClamAV for uploaded files (optional)

---

## 🧹 Cleanup & Lifecycle

### S3/MinIO Lifecycle Policies

```xml
<!-- S3 Lifecycle Policy -->
<LifecycleConfiguration>
  <Rule>
    <ID>DeleteFailedUploads</ID>
    <Filter>
      <Prefix>uploads/temp/</Prefix>
    </Filter>
    <Status>Enabled</Status>
    <Expiration>
      <Days>1</Days>
    </Expiration>
  </Rule>
  
  <Rule>
    <ID>ArchiveOldBooks</ID>
    <Filter>
      <Prefix>books/</Prefix>
    </Filter>
    <Status>Enabled</Status>
    <Transition>
      <Days>90</Days>
      <StorageClass>GLACIER</StorageClass>
    </Transition>
  </Rule>
</LifecycleConfiguration>
```

### Cleanup Job

```python
# app/tasks/cleanup.py
from celery import shared_task
from datetime import datetime, timedelta

@shared_task
def cleanup_failed_uploads():
    """
    Delete files from storage for failed/abandoned uploads
    """
    cutoff = datetime.utcnow() - timedelta(hours=24)
    
    failed_uploads = await db.query(FileUpload).filter(
        FileUpload.status.in_(['pending', 'failed']),
        FileUpload.created_at < cutoff
    ).all()
    
    storage = get_storage_service()
    
    for upload in failed_uploads:
        # Delete from storage
        storage.delete_file(upload.file_key)
        
        # Mark as deleted in DB
        upload.is_deleted = True
        upload.deleted_at = datetime.utcnow()
    
    await db.commit()
```

---

## ✅ Migration Checklist

- [ ] Add `file_uploads` table to database
- [ ] Add foreign key references to existing tables
- [ ] Implement `StorageService` class
- [ ] Create File Upload API endpoints
- [ ] Update Book Generation API to use presigned URLs
- [ ] Update User Management API for avatar uploads
- [ ] Configure MinIO/S3 bucket policies
- [ ] Set up lifecycle policies
- [ ] Update frontend to use new upload flow
- [ ] Test with both S3 and MinIO
- [ ] Set up monitoring and alerts
- [ ] Document API changes for frontend team

---

**Next Steps:**
1. Review this optimization plan
2. Decide on storage provider (S3 vs MinIO)
3. Implement database migration
4. Update API endpoints
5. Test thoroughly before deployment
