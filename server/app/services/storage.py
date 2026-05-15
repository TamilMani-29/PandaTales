"""Storage Service for MinIO/S3 operations with comprehensive error handling"""

import asyncio
import io
from datetime import timedelta
from pathlib import Path
from typing import BinaryIO, Literal
from uuid import UUID, uuid4

from fastapi import UploadFile as FastAPIUploadFile
from starlette.datastructures import UploadFile
from minio import Minio
from minio.error import S3Error

from app.common.exceptions import (
    BadRequestException,
    NotFoundException,
    ServiceUnavailableException,
)
from app.common.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class StorageService:
    """Service for handling file storage operations with MinIO/S3"""

    def __init__(self):
        """Initialize MinIO client"""
        try:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            self.bucket = settings.MINIO_BUCKET
        except Exception as e:
            logger.error("storage_init_error", error=str(e), exc_info=True)
            raise ServiceUnavailableException(
                message="Storage service initialization failed"
            )

    async def upload_file(
        self,
        file: UploadFile | BinaryIO,
        object_name: str,
        content_type: str | None = None,
        max_size_mb: int | None = None,
    ) -> str:
        """
        Upload file to MinIO with comprehensive error handling
        
        Args:
            file: File to upload (UploadFile or BinaryIO)
            object_name: Path/name in bucket (e.g., 'users/avatars/user123.jpg')
            content_type: MIME type (auto-detected if None)
            max_size_mb: Maximum file size in MB (None for no limit)
            
        Returns:
            str: Object name/path of uploaded file
            
        Raises:
            BadRequestException: Invalid file or size exceeded
            ServiceUnavailableException: Upload failed
        """
        try:
            # Read file content — UploadFile.read() is a coroutine in FastAPI
            if isinstance(file, UploadFile):
                if content_type is None:
                    content_type = file.content_type or "application/octet-stream"
                file_content = await file.read()
                await file.seek(0)
            else:
                # BinaryIO — synchronous read
                raw = file.read()
                # Guard: if somehow we got a coroutine (shouldn't happen), await it
                if asyncio.iscoroutine(raw):
                    file_content = await raw
                else:
                    file_content = raw
                if content_type is None:
                    content_type = "application/octet-stream"

            file_size = len(file_content)
            
            # Validate file size
            if max_size_mb is not None:
                max_size_bytes = max_size_mb * 1024 * 1024
                if file_size > max_size_bytes:
                    raise BadRequestException(
                        message=f"File size exceeds maximum allowed size of {max_size_mb}MB"
                    )
            
            if file_size == 0:
                raise BadRequestException(message="File is empty")
            
            # Upload to MinIO — run blocking SDK call off the event loop
            logger.info("uploading_file_to_minio", object_name=object_name, size_bytes=file_size, content_type=content_type)
            
            await asyncio.to_thread(
                self.client.put_object,
                self.bucket,
                object_name,
                io.BytesIO(file_content),
                file_size,
                content_type or "application/octet-stream",
            )
            
            logger.info("file_uploaded_successfully", object_name=object_name, size_bytes=file_size)
            return object_name
            
        except BadRequestException:
            # Re-raise validation errors
            raise
            
        except S3Error as e:
            logger.error(
                "minio_upload_error",
                object_name=object_name,
                error_code=e.code,
                error_message=e.message,
                exc_info=True,
            )
            
            if e.code == "NoSuchBucket":
                raise ServiceUnavailableException(
                    message="Storage bucket not found. Please contact support."
                )
            elif e.code == "AccessDenied":
                raise ServiceUnavailableException(
                    message="Storage access denied. Please contact support."
                )
            elif e.code == "EntityTooLarge":
                raise BadRequestException(
                    message="File is too large for storage system"
                )
            else:
                raise ServiceUnavailableException(
                    message="Failed to upload file. Please try again."
                )
                
        except Exception as e:
            logger.error("unexpected_upload_error", object_name=object_name, error=str(e), exc_info=True)
            raise ServiceUnavailableException(
                message="File upload failed due to unexpected error"
            )

    async def upload_image(
        self,
        file: UploadFile,
        prefix: Literal["avatars", "photos", "covers", "pages", "previews", "samples"],
        allowed_extensions: set[str] = {".jpg", ".jpeg", ".png", ".webp"},
        max_size_mb: int = 10,
        generate_filename: bool = True,
    ) -> str:
        """
        Upload image file with validation and standardized naming
        
        Args:
            file: Image file to upload
            prefix: Storage prefix (determines path structure)
            allowed_extensions: Allowed file extensions
            max_size_mb: Maximum file size in MB
            generate_filename: Whether to generate UUID-based filename
            
        Returns:
            str: Object name/path of uploaded image
            
        Raises:
            BadRequestException: Invalid image type or size
            ServiceUnavailableException: Upload failed
        """
        try:
            # Validate content type
            if not file.content_type or not file.content_type.startswith("image/"):
                raise BadRequestException(
                    message=f"Invalid file type. Expected image, got: {file.content_type}"
                )
            
            # Validate file extension
            file_ext = Path(file.filename or "").suffix.lower()
            if file_ext not in allowed_extensions:
                raise BadRequestException(
                    message=f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
                )
            
            # Generate object name based on prefix
            if generate_filename:
                filename = f"{uuid4()}{file_ext}"
            else:
                filename = file.filename or f"{uuid4()}{file_ext}"
            
            # Map prefix to storage path per MINIO_STORAGE_DESIGN.md
            prefix_map = {
                "avatars": "users/avatars",
                "photos": "users/uploads/photos",
                "covers": "generated/books/story/covers",  # Default to story
                "pages": "generated/books/story/pages",
                "previews": "templates/story-books/previews",
                "samples": "templates/story-books/samples",
            }
            
            object_name = f"{prefix_map[prefix]}/{filename}"
            
            # Upload file
            return await self.upload_file(
                file=file,
                object_name=object_name,
                content_type=file.content_type,
                max_size_mb=max_size_mb,
            )
            
        except BadRequestException:
            raise
        except ServiceUnavailableException:
            raise
        except Exception as e:
            logger.error("image_upload_error", error=str(e), exc_info=True)
            raise ServiceUnavailableException(
                message="Image upload failed"
            )

    async def upload_personalized_photo(
        self,
        file: "UploadFile",
        folder: str,
        index: int,
        max_size_mb: int = 10,
    ) -> str:
        """
        Upload a personalized order photo to a dedicated folder in MinIO.
        
        Object path: {folder}/photo_{index+1}{ext}
        e.g. personalized/arjun_abc123/photo_1.jpg

        Returns the object name stored in the DB.
        """
        from pathlib import Path as _Path
        from uuid import uuid4 as _uuid4

        if not file.content_type or not file.content_type.startswith("image/"):
            raise BadRequestException(
                message=f"Invalid file type for photo {index + 1}. Expected image, got: {file.content_type}"
            )

        file_ext = _Path(file.filename or "").suffix.lower()
        if file_ext not in {".jpg", ".jpeg", ".png", ".webp"}:
            file_ext = ".jpg"  # fallback for missing extension

        object_name = f"{folder}/photo_{index + 1}{file_ext}"
        return await self.upload_file(
            file=file,
            object_name=object_name,
            content_type=file.content_type,
            max_size_mb=max_size_mb,
        )

    async def get_file_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1),
        check_exists: bool = True,
        stat_timeout_seconds: float = 2.0,
    ) -> str:
        """
        Generate presigned URL for file access
        
        Args:
            object_name: Path/name in bucket
            expires: URL expiration time
            check_exists: Whether to verify object existence before signing URL
            stat_timeout_seconds: Timeout for object existence check when enabled
            
        Returns:
            str: Presigned URL
            
        Raises:
            NotFoundException: File not found
            ServiceUnavailableException: Failed to generate URL
        """
        try:
            # Optionally check object existence. For list views we can skip this to avoid
            # slow retries when MinIO is temporarily unavailable.
            if check_exists:
                try:
                    await asyncio.wait_for(
                        asyncio.to_thread(self.client.stat_object, self.bucket, object_name),
                        timeout=stat_timeout_seconds,
                    )
                except S3Error as e:
                    if e.code == "NoSuchKey":
                        raise NotFoundException(
                            message=f"File not found: {object_name}"
                        )
                    raise
                except asyncio.TimeoutError as exc:
                    logger.warning(
                        "minio_stat_timeout",
                        object_name=object_name,
                        timeout_seconds=stat_timeout_seconds,
                    )
                    raise ServiceUnavailableException(
                        message="Storage service is temporarily unavailable"
                    ) from exc
            
            # Generate presigned URL — run blocking SDK call off the event loop
            url = await asyncio.to_thread(
                self.client.presigned_get_object,
                self.bucket,
                object_name,
                expires,
            )
            
            logger.info("generated_presigned_url", object_name=object_name, expires_seconds=int(expires.total_seconds()))
            return url
            
        except NotFoundException:
            raise
            
        except S3Error as e:
            logger.error(
                "minio_url_generation_error",
                object_name=object_name,
                error_code=e.code,
                error_message=e.message,
                exc_info=True,
            )
            raise ServiceUnavailableException(
                message="Failed to generate file access URL"
            )
            
        except Exception as e:
            logger.error("unexpected_url_generation_error", object_name=object_name, error=str(e), exc_info=True)
            raise ServiceUnavailableException(
                message="Failed to generate file URL"
            )

    def get_public_file_url(self, object_name: str) -> str | None:
        """Build a browser-accessible object URL when public base URL is configured."""
        public_base = (settings.MINIO_PUBLIC_BASE_URL or "").strip().rstrip("/")
        if not public_base or not object_name:
            return None
        object_path = str(object_name).lstrip("/")
        return f"{public_base}/{self.bucket}/{object_path}"

    async def download_file(self, object_name: str) -> bytes:
        """
        Download file content from MinIO
        
        Args:
            object_name: Path/name in bucket
            
        Returns:
            bytes: File content
            
        Raises:
            NotFoundException: File not found
            ServiceUnavailableException: Download failed
        """
        try:
            # Download file — run blocking SDK call off the event loop
            response = await asyncio.to_thread(
                self.client.get_object,
                self.bucket,
                object_name,
            )
            
            # Read all data from response
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info("file_downloaded", object_name=object_name, size_bytes=len(data))
            return data
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise NotFoundException(
                    message=f"File not found: {object_name}"
                )
            logger.error(
                "minio_download_error",
                object_name=object_name,
                error_code=e.code,
                error_message=e.message,
                exc_info=True,
            )
            raise ServiceUnavailableException(
                message="Failed to download file"
            )
            
        except Exception as e:
            logger.error("unexpected_download_error", object_name=object_name, error=str(e), exc_info=True)
            raise ServiceUnavailableException(
                message="File download failed"
            )

    async def delete_file(self, object_name: str) -> bool:
        """
        Delete file from MinIO
        
        Args:
            object_name: Path/name in bucket
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            ServiceUnavailableException: Deletion failed
        """
        try:
            await asyncio.to_thread(self.client.remove_object, self.bucket, object_name)
            logger.info("file_deleted", object_name=object_name)
            return True
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                logger.warning("file_not_found_for_deletion", object_name=object_name)
                return False
                
            logger.error(
                "minio_delete_error",
                object_name=object_name,
                error_code=e.code,
                error_message=e.message,
                exc_info=True,
            )
            raise ServiceUnavailableException(
                message="Failed to delete file"
            )
            
        except Exception as e:
            logger.error("unexpected_delete_error", object_name=object_name, error=str(e), exc_info=True)
            raise ServiceUnavailableException(
                message="File deletion failed"
            )

    async def file_exists(self, object_name: str) -> bool:
        """
        Check if file exists in MinIO
        
        Args:
            object_name: Path/name in bucket
            
        Returns:
            bool: True if file exists
        """
        try:
            await asyncio.to_thread(self.client.stat_object, self.bucket, object_name)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            logger.error("file_exists_check_error", object_name=object_name, error=str(e), exc_info=True)
            return False
        except Exception as e:
            logger.error("unexpected_file_exists_error", object_name=object_name, error=str(e), exc_info=True)
            return False

    async def get_public_url(self, object_name: str) -> str:
        """
        Get public URL for files in public paths (templates/*, public/*)
        
        Args:
            object_name: Path/name in bucket
            
        Returns:
            str: Public URL (no expiration)
        """
        # Per MINIO_STORAGE_DESIGN.md, public paths don't need presigned URLs
        if object_name.startswith(("templates/", "public/")):
            return f"http://{settings.MINIO_ENDPOINT}/{self.bucket}/{object_name}"
        else:
            # For private files, return presigned URL with 7-day expiration
            return await self.get_file_url(object_name, expires=timedelta(days=7))


def get_storage_service() -> StorageService:
    """Dependency for FastAPI endpoints"""
    return StorageService()
