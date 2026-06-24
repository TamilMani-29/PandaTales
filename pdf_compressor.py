# ============================================================
# PandaTales — PDF Compression Utility
# File: server/app/utils/pdf_compressor.py
#
# WHERE TO ADD THIS FILE:
#   server/app/utils/pdf_compressor.py  ← create this file
#
# WHAT THIS HANDLES:
#   1. Compresses already-generated PDFs (for existing books on AWS)
#   2. Shows how to build PDFs with compressed images from the start
#
# DEPENDENCIES:
#   pip install pypdf pillow reportlab
#   (pypdf is lightweight — add to server/requirements.txt)
# ============================================================

import io
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ── Strategy 1: Compress an existing PDF ─────────────────────
# Use this to compress PDFs already stored in MinIO/R2

def compress_existing_pdf(pdf_bytes: bytes, image_quality: int = 82) -> tuple[bytes, dict]:
    """
    Re-compress all images inside an existing PDF.
    Works on already-generated book PDFs.

    WHERE TO CALL:
      Option A: Run once as a batch job on all existing PDFs in storage.
      Option B: Call in the book generation task after PDF is built.

    USAGE:
      compressed_pdf, stats = compress_existing_pdf(original_pdf_bytes)
      storage.upload_file(compressed_pdf, f"books/{book_id}/full.pdf")

    RETURNS: (compressed_bytes, stats_dict)
    SAVING: Typically 60-80% for PDFs containing raw PNG/BMP images.

    REQUIRES: pip install pypdf pillow
    """
    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import DecodedStreamObject, EncodedStreamObject
        from PIL import Image

        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()

        total_images = 0
        compressed_images = 0
        bytes_saved = 0

        for page_num, page in enumerate(reader.pages):
            writer.add_page(page)

            # Find image XObjects on this page
            if "/Resources" not in page:
                continue
            resources = page["/Resources"]
            if "/XObject" not in resources:
                continue

            xobjects = resources["/XObject"].get_object()
            for obj_name, obj_ref in xobjects.items():
                obj = obj_ref.get_object()

                if obj.get("/Subtype") != "/Image":
                    continue

                total_images += 1
                original_bytes = obj.get_data()
                original_size = len(original_bytes)

                try:
                    # Detect image format
                    filter_type = obj.get("/Filter")
                    colorspace = obj.get("/ColorSpace", "/DeviceRGB")

                    # Skip already-compressed small images
                    if original_size < 20 * 1024:  # skip if under 20KB
                        continue

                    # Load and recompress
                    img = Image.open(io.BytesIO(original_bytes))
                    if img.mode not in ("RGB", "L"):
                        img = img.convert("RGB")

                    # Re-encode as JPEG
                    output = io.BytesIO()
                    img.save(output, format="JPEG", quality=image_quality, optimize=True)
                    new_bytes = output.getvalue()
                    new_size = len(new_bytes)

                    # Only use if actually smaller
                    if new_size < original_size * 0.95:
                        obj._data = new_bytes
                        obj.update({
                            "/Filter": "/DCTDecode",
                            "/Length": new_size,
                        })
                        bytes_saved += original_size - new_size
                        compressed_images += 1

                except Exception as img_err:
                    logger.debug(f"Skipping image on page {page_num}: {img_err}")
                    continue

        # Write compressed PDF
        output_buf = io.BytesIO()
        writer.write(output_buf)
        compressed_pdf = output_buf.getvalue()

        stats = {
            "original_size_kb": len(pdf_bytes) // 1024,
            "compressed_size_kb": len(compressed_pdf) // 1024,
            "saving_percent": round((1 - len(compressed_pdf) / len(pdf_bytes)) * 100),
            "total_images": total_images,
            "compressed_images": compressed_images,
            "bytes_saved_kb": bytes_saved // 1024,
        }

        logger.info(
            f"PDF compressed: {stats['original_size_kb']}KB → "
            f"{stats['compressed_size_kb']}KB "
            f"({stats['saving_percent']}% saved, "
            f"{compressed_images}/{total_images} images recompressed)"
        )

        return compressed_pdf, stats

    except ImportError:
        logger.error("pypdf not installed. Run: pip install pypdf")
        return pdf_bytes, {}
    except Exception as e:
        logger.error(f"PDF compression failed: {e}. Returning original.")
        return pdf_bytes, {}


# ── Strategy 2: Batch compress all PDFs in R2 ─────────────────
# Run this ONCE as a migration job on your existing book PDFs

async def batch_compress_all_books():
    """
    One-time job to compress all existing book PDFs in R2/MinIO.

    HOW TO RUN (one time, from server shell):
      docker-compose exec backend python -c "
        import asyncio
        from app.utils.pdf_compressor import batch_compress_all_books
        asyncio.run(batch_compress_all_books())
      "

    OR add as a Celery task and trigger manually once.
    """
    from app.core.storage import storage

    # List all PDF keys in storage
    response = storage.client.list_objects_v2(
        Bucket=storage.bucket,
        Prefix="books/",
    )

    pdf_keys = [
        obj["Key"]
        for obj in response.get("Contents", [])
        if obj["Key"].endswith("/full.pdf")
    ]

    logger.info(f"Found {len(pdf_keys)} book PDFs to compress")

    total_saved_kb = 0
    for key in pdf_keys:
        try:
            pdf_bytes = storage.download_file(key)
            compressed, stats = compress_existing_pdf(pdf_bytes)

            if stats.get("saving_percent", 0) > 10:
                storage.upload_file(compressed, key, "application/pdf")
                saved = stats.get("bytes_saved_kb", 0)
                total_saved_kb += saved
                logger.info(f"  Compressed {key}: {stats['saving_percent']}% saved")
            else:
                logger.info(f"  Skipped {key}: already well-compressed")

        except Exception as e:
            logger.error(f"  Failed {key}: {e}")

    logger.info(f"Batch complete. Total saved: {total_saved_kb // 1024} MB")


# ── Strategy 3: Build PDF with compression from the start ─────
# This is the cleanest approach — use when implementing PDF generation

def build_optimised_book_pdf(
    pages: list[dict],
    title: str,
    author_name: str = "PandaTales",
) -> bytes:
    """
    Build a book PDF with images pre-compressed as JPEG.
    Much smaller than embedding raw PNG from the start.

    WHERE TO CALL:
      server/app/utils/pdf_generator.py  (when you implement this)
      Replace raw image embedding with this function.

    USAGE:
      pages = [
          {"text": "Once upon a time...", "image_bytes": <webp/png bytes>},
          {"text": "The child ran...", "image_bytes": <webp/png bytes>},
          ...
      ]
      pdf_bytes = build_optimised_book_pdf(pages, title="Emma's Adventure")
      storage.upload_file(pdf_bytes, f"books/{book_id}/full.pdf")

    REQUIRES: pip install reportlab pillow
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.utils import ImageReader
        from PIL import Image

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4  # 595 x 842 points

        for page_data in pages:
            text = page_data.get("text", "")
            image_bytes = page_data.get("image_bytes")

            # Add image if present
            if image_bytes:
                # Convert to JPEG for embedding (WebP not supported in PDF)
                img = Image.open(io.BytesIO(image_bytes))
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Resize for page
                img.thumbnail((int(width - 80), int(height * 0.65)), Image.LANCZOS)

                jpeg_buf = io.BytesIO()
                img.save(jpeg_buf, format="JPEG", quality=82, optimize=True)
                jpeg_buf.seek(0)

                img_reader = ImageReader(jpeg_buf)
                img_w, img_h = img.size
                x = (width - img_w) / 2
                c.drawImage(img_reader, x, height - img_h - 40, img_w, img_h)

            # Add text
            if text:
                c.setFont("Helvetica", 13)
                text_y = 120
                # Simple word wrap
                words = text.split()
                line = ""
                for word in words:
                    test_line = f"{line} {word}".strip()
                    if c.stringWidth(test_line, "Helvetica", 13) < width - 80:
                        line = test_line
                    else:
                        c.drawCentredString(width / 2, text_y, line)
                        text_y -= 20
                        line = word
                if line:
                    c.drawCentredString(width / 2, text_y, line)

            c.showPage()

        c.save()
        pdf_bytes = buf.getvalue()
        logger.info(f"Built optimised PDF: {len(pdf_bytes)//1024}KB, {len(pages)} pages")
        return pdf_bytes

    except ImportError:
        logger.error("reportlab not installed. Run: pip install reportlab")
        return b""
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return b""
