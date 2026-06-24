# ============================================================
# PandaTales — Exact Code Changes for Template Upload
# File: server/app/api/v1/templates.py
#
# This file shows EXACTLY what Tamil Mani needs to change/add
# in the existing templates.py upload endpoint.
#
# Search for the upload handler (POST endpoint that receives
# an image file) and apply the 3 changes marked below.
# ============================================================


# ── CHANGE 1: Add import at top of templates.py ──────────────
# Add this line with the other imports at the top of the file:

from app.utils.compression import (
    compress_template_image,
    compress_collection_cover,
    generate_thumbnail,
    validate_upload_size,
)


# ── CHANGE 2: In the image upload endpoint ───────────────────
# Find your upload endpoint. It will look something like this:
#
#   @router.post("/{template_id}/images")
#   async def upload_template_image(
#       template_id: UUID,
#       file: UploadFile = File(...),
#       ...
#   ):
#
# BEFORE (what it probably does now):
#
#   image_bytes = await file.read()
#   key = f"templates/{template_id}/cover.png"
#   url = storage.upload_file(image_bytes, key, file.content_type)
#   return {"url": url}
#
#
# AFTER (add these 4 lines, change 1 line):

async def upload_template_image_EXAMPLE(file, template_id, storage):
    """
    Example showing exactly what to change in your upload handler.
    This is NOT a complete endpoint — just the relevant section.
    """
    image_bytes = await file.read()

    # ADD THIS: reject oversized uploads before any processing
    ok, error_msg = validate_upload_size(image_bytes)
    if not ok:
        raise ValueError(f"Upload too large: {error_msg}")    # use HTTPException in FastAPI

    # ADD THIS: compress the image
    compressed = compress_template_image(image_bytes)

    # CHANGE THIS: use compressed.data and compressed.content_type
    # instead of raw image_bytes and file.content_type
    key = f"templates/{template_id}/cover.webp"               # ← change extension to .webp
    url = storage.upload_file(
        compressed.data,            # ← was: image_bytes
        key,
        compressed.content_type,    # ← was: file.content_type
    )

    # ADD THIS: also generate and store a thumbnail
    thumbnail = generate_thumbnail(image_bytes)               # use original, not compressed
    thumb_key = f"templates/{template_id}/thumb.webp"
    thumb_url = storage.upload_file(thumbnail.data, thumb_key, thumbnail.content_type)

    return {
        "url": url,
        "thumbnail_url": thumb_url,
        "original_size_kb": compressed.original_size_kb,      # optional: log for monitoring
        "compressed_size_kb": compressed.compressed_size_kb,
        "saving_percent": compressed.saving_percent,
    }


# ── CHANGE 3: In book generation Celery task ─────────────────
# Find server/app/tasks/book_generation_task.py (once implemented)
# In the page generation loop, add compression after each AI image:

def generate_page_EXAMPLE(book_id, page_num, openai_image_bytes, storage):
    """
    Example showing compression in the AI generation pipeline.
    """
    from app.utils.compression import compress_ai_page_image, prepare_image_for_pdf

    # Compress AI image for storage (WebP)
    compressed = compress_ai_page_image(openai_image_bytes)

    # Store compressed WebP in R2 (for display in app)
    page_key = f"books/{book_id}/pages/page_{page_num}.webp"
    page_url = storage.upload_file(
        compressed.data,
        page_key,
        compressed.content_type,
    )

    # Also prepare JPEG version for PDF embedding
    # (store separately, used when building the final PDF)
    pdf_image_bytes = prepare_image_for_pdf(openai_image_bytes)
    pdf_key = f"books/{book_id}/pages/page_{page_num}_pdf.jpg"
    storage.upload_file(pdf_image_bytes, pdf_key, "image/jpeg")

    return page_url


# ── CHANGE 4: After generation completes, delete user photos ─
# At the END of generate_book_task, after PDF is built:

def cleanup_after_generation_EXAMPLE(book_id, uploaded_photo_keys, storage):
    """
    Delete raw user uploads after book generation is complete.
    Called at the very end of generate_book_task.
    """
    from app.utils.compression import ImageConfig

    if uploaded_photo_keys:
        deleted = storage.delete_files(uploaded_photo_keys)
        logger.info(f"Cleaned up {deleted} user photos for book {book_id}")
