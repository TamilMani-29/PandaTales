"""Helpers for reversible PDF compression in object storage."""

from __future__ import annotations

import gzip
from pathlib import Path

from app.common.logging import get_logger

logger = get_logger(__name__)

PDF_GZIP_SUFFIX = ".pdf.gz"


def to_pdf_storage_object_name(object_name: str) -> str:
    """Return object path used for compressed PDF blobs in storage."""
    if object_name.lower().endswith(PDF_GZIP_SUFFIX):
        return object_name
    if object_name.lower().endswith(".pdf"):
        return f"{object_name}.gz"
    return f"{object_name}.pdf.gz"


def to_pdf_download_filename(object_name: str, fallback: str = "book.pdf") -> str:
    """Return a user-facing filename with a .pdf extension."""
    name = Path(object_name).name or fallback
    if name.lower().endswith(".pdf.gz"):
        return name[:-3]
    if name.lower().endswith(".gz"):
        return Path(name).stem
    if name.lower().endswith(".pdf"):
        return name
    return fallback


def compress_pdf_for_storage(pdf_bytes: bytes, *, compresslevel: int = 9) -> bytes:
    """Compress PDF bytes for storage using gzip (lossless)."""
    if not pdf_bytes:
        return pdf_bytes
    return gzip.compress(pdf_bytes, compresslevel=compresslevel, mtime=0)


def maybe_decompress_pdf(payload: bytes, *, object_name: str | None = None) -> bytes:
    """Decompress gzip payload when needed, otherwise return bytes unchanged."""
    if not payload:
        return payload

    looks_gzip = payload[:2] == b"\x1f\x8b"
    should_try = looks_gzip or (object_name or "").lower().endswith(".gz")
    if not should_try:
        return payload

    try:
        return gzip.decompress(payload)
    except OSError:
        logger.warning("pdf_decompress_failed_returning_original", object_name=object_name)
        return payload
