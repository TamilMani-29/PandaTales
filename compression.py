# ============================================================
# PandaTales — Compression Middleware
# File: server/app/utils/compression.py
#
# WHERE TO ADD THIS FILE:
#   server/app/utils/compression.py   ← create this file
#
# WHAT THIS HANDLES:
#   1. Admin/you uploads template images → compress to WebP
#   2. User uploads child photos → cap size before processing
#   3. AI-generated page images → compress before storing in R2
#   4. PDF generation → embed compressed JPEGs not raw PNGs
#
# DEPENDENCIES (already in your stack):
#   - Pillow  (pip install Pillow)
#   - pypdf   (pip install pypdf)    ← for PDF compression
#   No new packages needed.
# ============================================================

import io
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


# ── Config constants ──────────────────────────────────────────
# Change these values in one place — affects entire app

class ImageConfig:
    # Template images you upload (book cover, page backgrounds, collection images)
    TEMPLATE_MAX_SIZE   = (1200, 1600)   # px — A4 proportions, crisp on screen
    TEMPLATE_QUALITY    = 85             # WebP quality (85 = visually lossless)

    # User-uploaded child photos (before face compositing)
    UPLOAD_MAX_SIZE     = (1600, 1600)   # cap — no quality loss, just size limit
    UPLOAD_QUALITY      = 92            # high quality for face processing accuracy

    # AI-generated page illustrations (from OpenAI DALL-E)
    AI_PAGE_MAX_SIZE    = (1024, 1024)   # match OpenAI output size
    AI_PAGE_QUALITY     = 82            # balance quality vs size

    # Thumbnail for book listing/preview pages
    THUMBNAIL_MAX_SIZE  = (400, 560)    # small — only used in grids
    THUMBNAIL_QUALITY   = 78

    # Collection cover image shown on homepage
    COLLECTION_MAX_SIZE = (800, 600)
    COLLECTION_QUALITY  = 82

    # Max upload size allowed from browser (reject before processing)
    MAX_UPLOAD_BYTES    = 15 * 1024 * 1024   # 15 MB hard limit


class PDFConfig:
    # Image quality when embedding into final book PDF
    # JPEG is used inside PDF (not WebP — PDF spec doesn't support WebP)
    EMBED_JPEG_QUALITY  = 82
    EMBED_MAX_SIZE      = (1200, 1600)   # resized before embedding


# ── Result dataclass ──────────────────────────────────────────

@dataclass
class CompressionResult:
    data: bytes
    content_type: str
    original_size_kb: int
    compressed_size_kb: int
    saving_percent: int
    format: str


# ── Core compression function ─────────────────────────────────

def _compress_image(
    image_bytes: bytes,
    max_size: tuple[int, int],
    quality: int,
    output_format: str = "WEBP",
    force_rgb: bool = True,
) -> CompressionResult:
    """
    Internal: compress image bytes to target format/size/quality.
    Returns CompressionResult with compressed bytes + metadata.
    """
    original_size = len(image_bytes)

    try:
        img = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if needed (required for JPEG, recommended for WebP)
        if force_rgb and img.mode in ("RGBA", "P", "LA", "L"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode in ("RGBA", "LA"):
                alpha = img.convert("RGBA").split()[3]
                background.paste(img.convert("RGBA"), mask=alpha)
            elif img.mode == "P":
                background.paste(img.convert("RGBA"))
            else:
                background.paste(img.convert("RGB"))
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize only if larger than max (never upscale)
        if img.width > max_size[0] or img.height > max_size[1]:
            img.thumbnail(max_size, Image.LANCZOS)

        # Compress
        output = io.BytesIO()
        if output_format == "WEBP":
            img.save(output, format="WEBP", quality=quality, method=4)
            content_type = "image/webp"
        elif output_format == "JPEG":
            img.save(output, format="JPEG", quality=quality, optimize=True)
            content_type = "image/jpeg"
        else:
            img.save(output, format=output_format)
            content_type = f"image/{output_format.lower()}"

        compressed = output.getvalue()
        compressed_size = len(compressed)
        saving = round((1 - compressed_size / original_size) * 100) if original_size > 0 else 0

        logger.info(
            f"Compressed image [{output_format}]: "
            f"{original_size//1024}KB → {compressed_size//1024}KB "
            f"({saving}% saved, max={max_size}, q={quality})"
        )

        return CompressionResult(
            data=compressed,
            content_type=content_type,
            original_size_kb=original_size // 1024,
            compressed_size_kb=compressed_size // 1024,
            saving_percent=saving,
            format=output_format,
        )

    except Exception as e:
        logger.error(f"Compression failed: {e}. Returning original bytes.")
        return CompressionResult(
            data=image_bytes,
            content_type="image/png",
            original_size_kb=original_size // 1024,
            compressed_size_kb=original_size // 1024,
            saving_percent=0,
            format="original",
        )


# ── Public API — one function per use case ────────────────────
# Tamil Mani: call these functions at the exact points described below

def compress_template_image(image_bytes: bytes) -> CompressionResult:
    """
    WHERE TO CALL:
      In the template upload API endpoint, right before storing to R2.

    CURRENT CODE LOCATION (once implemented):
      server/app/api/v1/templates.py
      → POST /api/v1/templates/{id}/images
      → Before: storage.upload_file(raw_bytes, key)
      → After:  result = compress_template_image(raw_bytes)
                storage.upload_file(result.data, key, result.content_type)

    USE CASE:
      Admin uploads book cover image, background art, collection images.
      These are stored once, served millions of times.

    SAVING: ~50% per template image.
    """
    return _compress_image(
        image_bytes,
        ImageConfig.TEMPLATE_MAX_SIZE,
        ImageConfig.TEMPLATE_QUALITY,
        output_format="WEBP",
    )


def compress_collection_cover(image_bytes: bytes) -> CompressionResult:
    """
    WHERE TO CALL:
      When uploading collection cover images shown on homepage/catalog.

    CURRENT CODE LOCATION:
      server/app/api/v1/collections.py (when implemented)
      → POST /api/v1/collections/{id}/cover

    SAVING: ~55% per collection cover.
    """
    return _compress_image(
        image_bytes,
        ImageConfig.COLLECTION_MAX_SIZE,
        ImageConfig.COLLECTION_QUALITY,
        output_format="WEBP",
    )


def compress_user_upload(image_bytes: bytes) -> CompressionResult:
    """
    WHERE TO CALL:
      When user uploads child photo for personalisation.
      Call BEFORE storing — but AFTER virus/malware check.

    CURRENT CODE LOCATION (once book generation is implemented):
      server/app/api/v1/books.py
      → POST /api/v1/books/generate
      → In the photo upload handler, before saving temp upload

    NOTE: Keep quality HIGH (92) — face processing accuracy depends on it.
    This is NOT for permanent storage — delete after generation completes.

    SAVING: ~35% on upload temp storage.
    """
    return _compress_image(
        image_bytes,
        ImageConfig.UPLOAD_MAX_SIZE,
        ImageConfig.UPLOAD_QUALITY,
        output_format="WEBP",
    )


def compress_ai_page_image(image_bytes: bytes) -> CompressionResult:
    """
    WHERE TO CALL:
      In the Celery book generation task, after each OpenAI image is received,
      before storing the page image to R2.

    CURRENT CODE LOCATION (once implemented):
      server/app/tasks/book_generation_task.py
      → Inside generate_book_task(), in the page generation loop
      → After: image_bytes = openai_client.images.generate(...)
      → Add:   compressed = compress_ai_page_image(image_bytes)
               page_url = storage.upload_file(compressed.data, key, compressed.content_type)

    SAVING: ~50% per AI image. For a 20-page book: ~30MB → ~3MB.
    """
    return _compress_image(
        image_bytes,
        ImageConfig.AI_PAGE_MAX_SIZE,
        ImageConfig.AI_PAGE_QUALITY,
        output_format="WEBP",
    )


def generate_thumbnail(image_bytes: bytes) -> CompressionResult:
    """
    WHERE TO CALL:
      After generating/storing the book cover image.
      Store thumbnail separately — used in book listing grids.

    CURRENT CODE LOCATION:
      server/app/tasks/book_generation_task.py
      → After cover image is generated and stored
      → Add: thumb = generate_thumbnail(cover_bytes)
             storage.upload_file(thumb.data, f"books/{book_id}/thumb.webp", thumb.content_type)

    SAVING: ~90% vs full cover — thumbnails are tiny.
    """
    return _compress_image(
        image_bytes,
        ImageConfig.THUMBNAIL_MAX_SIZE,
        ImageConfig.THUMBNAIL_QUALITY,
        output_format="WEBP",
    )


def prepare_image_for_pdf(image_bytes: bytes) -> bytes:
    """
    WHERE TO CALL:
      In the PDF generation step, when embedding images into the final book PDF.
      PDFs do not support WebP — images must be JPEG inside PDF.

    CURRENT CODE LOCATION (once PDF generation is implemented):
      server/app/utils/pdf_generator.py
      → When building each page of the PDF
      → Instead of: pdf.add_image(raw_png_bytes)
      → Use:        jpeg_bytes = prepare_image_for_pdf(page_image_bytes)
                    pdf.add_image(jpeg_bytes)  # much smaller PDF

    CRITICAL: This is the single biggest PDF size reduction.
    Raw PNG images inside PDF = 60MB book. JPEG 82% = 4MB book.
    """
    result = _compress_image(
        image_bytes,
        ImageConfig.EMBED_MAX_SIZE,
        ImageConfig.EMBED_JPEG_QUALITY,
        output_format="JPEG",   # ← must be JPEG for PDF embedding
    )
    return result.data


def validate_upload_size(image_bytes: bytes) -> tuple[bool, str]:
    """
    WHERE TO CALL:
      Very first check when any image upload arrives at the API.
      Reject before any processing happens.

    CURRENT CODE LOCATION:
      server/app/api/v1/templates.py  (and any other upload endpoint)
      → First line of the upload handler:
        ok, msg = validate_upload_size(file_bytes)
        if not ok:
            raise HTTPException(status_code=413, detail=msg)

    Returns (True, "") if valid, (False, error_message) if too large.
    """
    size = len(image_bytes)
    if size > ImageConfig.MAX_UPLOAD_BYTES:
        mb = size / 1024 / 1024
        limit_mb = ImageConfig.MAX_UPLOAD_BYTES / 1024 / 1024
        return False, f"File too large: {mb:.1f}MB. Maximum allowed: {limit_mb:.0f}MB."
    return True, ""
