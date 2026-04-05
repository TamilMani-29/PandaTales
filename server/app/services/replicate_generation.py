"""Replicate AI Image Generation Service

Handles calling the Replicate img2img API to generate storybook pages in parallel,
polling for completion, and storing results in MinIO.
"""

import asyncio
import base64
import io
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes

from app.common.logging import get_logger
from app.core.config import settings
from app.repositories.generated_book import GeneratedBookRepository
from app.repositories.story_book_template import StoryBookTemplateRepository
from app.services.storage import StorageService
from app.services.text_overlay import TextOverlayService

logger = get_logger(__name__)

REPLICATE_API_BASE = "https://api.replicate.com/v1"


class ReplicateGenerationService:
    """Service to interact with Replicate API for storybook image generation."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = GeneratedBookRepository(db)
        self.template_repository = StoryBookTemplateRepository(db)
        self.storage = StorageService()
        self.text_overlay = TextOverlayService()
        self._headers = {
            "Authorization": f"Token {settings.REPLICATE_API_TOKEN}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def start_story_book_generation(
        self,
        book_id: UUID,
        reference_photo_object: str,
        prompts_config: dict[str, Any],
        child_name: str,
        child_gender: str,
    ) -> None:
        """
        Start parallel Replicate predictions for all pages in the book.

        Fires all predictions (up to MAX_PARALLEL_GENERATIONS concurrently),
        then stores the prediction IDs in the book record and returns immediately.
        The polling endpoint will pick up progress afterwards.
        """
        pages: list[dict] = prompts_config.get("pages", [])
        if not pages:
            logger.error("no_pages_in_prompts_config", book_id=str(book_id))
            await self._mark_failed(book_id, "NO_PAGES", "No page prompts configured in template")
            return

        # TESTING: Limit pages if TEST_PAGE_LIMIT is set
        if settings.TEST_PAGE_LIMIT is not None and settings.TEST_PAGE_LIMIT > 0:
            original_count = len(pages)
            pages = pages[:settings.TEST_PAGE_LIMIT]
            logger.info(
                "test_page_limit_applied",
                book_id=str(book_id),
                original_pages=original_count,
                limited_pages=len(pages),
            )

        # Download image from MinIO and convert to base64 data URI
        # This avoids localhost URL issues when Replicate tries to download
        try:
            image_data = await self.storage.download_file(reference_photo_object)
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            # Replicate supports data URIs
            reference_url = f"data:image/jpeg;base64,{image_base64}"
            logger.info(
                "converted_image_to_data_uri",
                book_id=str(book_id),
                object_name=reference_photo_object,
                size_bytes=len(image_data),
            )
        except Exception as exc:
            logger.error("failed_to_convert_image", book_id=str(book_id), error=str(exc))
            await self._mark_failed(book_id, "STORAGE_ERROR", "Failed to download and convert reference photo")
            return

        semaphore = asyncio.Semaphore(settings.MAX_PARALLEL_GENERATIONS)

        async def _start_one(page: dict, stagger_delay: float) -> tuple[int, str | None]:
            page_number: int = page["page_number"]
            prompt = self._build_prompt(page, child_name, child_gender)
            # Stagger starts so we don't slam the API with simultaneous requests
            await asyncio.sleep(stagger_delay)
            async with semaphore:
                return page_number, await self._create_prediction(prompt, reference_url)

        # Use configurable stagger delay between predictions to avoid rate-limiting
        tasks = [_start_one(p, i * settings.REPLICATE_STAGGER_SECONDS) for i, p in enumerate(pages)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build the prediction map: {"page_0": {"prediction_id": ..., "status": "starting"}}
        prediction_map: dict[str, Any] = {}
        failed_pages = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("prediction_start_error", book_id=str(book_id), error=str(result))
                failed_pages.append(str(result))
                continue
            page_number, pred_id = result
            key = f"page_{page_number - 1}"
            if pred_id:
                prediction_map[key] = {
                    "prediction_id": pred_id,
                    "status": "starting",
                    "page_number": page_number,
                    "image_object": None,
                }
            else:
                failed_pages.append(f"page_{page_number}")

        if not prediction_map:
            logger.error(
                "all_predictions_failed_to_start",
                book_id=str(book_id),
                total_pages=len(pages),
                failed_count=len(failed_pages),
            )
            await self._mark_failed(book_id, "ALL_PREDICTIONS_FAILED", "All page predictions failed to start")
            return

        # Persist prediction IDs
        book = await self.repository.get_by_id(book_id)
        if book:
            book.replicate_prediction_ids = prediction_map
            # Flag JSONB field as modified
            attributes.flag_modified(book, "replicate_prediction_ids")
            book.total_pages = len(pages)
            book.status = "processing"
            book.progress = 5
            book.current_step = "image_generation"
            book.generation_steps = {
                "photo_processing": "completed",
                "story_generation": "completed",
                "image_generation": "in_progress",
                "pdf_generation": "pending",
            }
            await self.db.flush()

        logger.info(
            "predictions_started",
            book_id=str(book_id),
            total_pages=len(pages),
            prediction_count=len(prediction_map),
            failed_count=len(failed_pages),
            success_rate=f"{len(prediction_map)}/{len(pages)}",
        )

    # ------------------------------------------------------------------
    # Polling (called by status endpoint)
    # ------------------------------------------------------------------

    async def poll_and_update(self, book_id: UUID) -> dict[str, Any]:
        """
        Poll Replicate for all pending predictions associated with a book.

        Updates the book record in DB for each completed prediction and
        returns a status summary dict with keys:
          - status: "processing" | "completed" | "failed"
          - progress: int 0-100
          - completed_pages: list[int]
          - preview_pages: list[dict] (page_number, image_url)
        """
        book = await self.repository.get_by_id(book_id)
        if not book or not book.replicate_prediction_ids:
            return {"status": "processing", "progress": 0, "completed_pages": [], "preview_pages": []}

        # Fetch template to get prompts_config for story_line text
        template = await self.template_repository.get_by_id(book.template_id)
        prompts_config = template.prompts_config if template and template.prompts_config else {}
        pages_data = prompts_config.get("pages", [])
        
        # Build lookup map: page_number -> page_data (contains story_line)
        pages_map = {page["page_number"]: page for page in pages_data if "page_number" in page}

        prediction_map: dict[str, Any] = dict(book.replicate_prediction_ids)
        total = len(prediction_map)
        changed = False

        async with httpx.AsyncClient(timeout=30) as client:
            for key, info in prediction_map.items():
                pred_id = info.get("prediction_id")
                if not pred_id:
                    continue

                current_status = info.get("status")
                
                # Skip if already failed/canceled
                if current_status in ("failed", "canceled"):
                    continue
                
                # For succeeded predictions, check if image was downloaded
                if current_status == "succeeded":
                    # Retry download if image_object is missing
                    if not info.get("image_object"):
                        logger.info(
                            "retrying_image_download",
                            book_id=str(book_id),
                            key=key,
                            pred_id=pred_id,
                        )
                        # Re-fetch the prediction to get the image URL
                        result = await self._poll_prediction(client, pred_id)
                        output = result.get("output")
                        image_url = output[0] if isinstance(output, list) and output else output
                        if image_url:
                            page_number = info.get("page_number")
                            page_data = pages_map.get(page_number, {})
                            object_name = await self._download_and_store(
                                image_url, book_id, key, page_data, book.child_name, book.child_gender
                            )
                            if object_name:
                                info["image_object"] = object_name
                                changed = True
                                logger.info(
                                    "image_download_retry_success",
                                    book_id=str(book_id),
                                    key=key,
                                )
                    continue  # Already terminal, skip polling

                # Poll for status update
                result = await self._poll_prediction(client, pred_id)
                status = result.get("status", "")
                info["status"] = status

                if status == "succeeded":
                    output = result.get("output")
                    image_url = output[0] if isinstance(output, list) and output else output
                    if image_url:
                        page_number = info.get("page_number")
                        page_data = pages_map.get(page_number, {})
                        object_name = await self._download_and_store(
                            image_url, book_id, key, page_data, book.child_name, book.child_gender
                        )
                        if object_name:
                            info["image_object"] = object_name
                            changed = True
                        else:
                            logger.error(
                                "image_download_failed",
                                book_id=str(book_id),
                                key=key,
                                image_url=image_url[:100],
                            )
                    else:
                        logger.error(
                            "prediction_no_output",
                            book_id=str(book_id),
                            key=key,
                            pred_id=pred_id,
                        )
                elif status == "failed":
                    error_detail = result.get("error", "Unknown error")
                    logger.warning(
                        "prediction_failed", 
                        book_id=str(book_id), 
                        key=key, 
                        pred_id=pred_id,
                        error=error_detail,
                    )
                    changed = True

        # Recount completed
        completed = [k for k, v in prediction_map.items() if v.get("status") == "succeeded"]
        failed_preds = [k for k, v in prediction_map.items() if v.get("status") in ("failed", "canceled")]
        progress = int((len(completed) / total) * 90) + 5  # 5–95%

        # Build preview_pages from completed pages (sorted by page number)
        preview_pages: list[dict] = []
        for key, info in sorted(prediction_map.items(), key=lambda x: x[1].get("page_number", 0)):
            if info.get("image_object"):
                try:
                    img_url = await self.storage.get_file_url(
                        info["image_object"], expires=timedelta(hours=24)
                    )
                    preview_pages.append({
                        "page_number": info.get("page_number", 0),
                        "image_url": img_url,
                        "text": None,
                    })
                    logger.info(
                        "preview_page_added",
                        book_id=str(book_id),
                        key=key,
                        page_number=info.get("page_number", 0),
                    )
                except Exception as exc:
                    logger.error(
                        "presigned_url_generation_failed",
                        book_id=str(book_id),
                        key=key,
                        object_name=info.get("image_object"),
                        error=str(exc),
                    )

        # Always update prediction map and preview pages (even if unchanged)
        # This ensures preview_pages is available as soon as images are generated
        book.replicate_prediction_ids = prediction_map
        # Flag JSONB field as modified so SQLAlchemy persists the changes
        attributes.flag_modified(book, "replicate_prediction_ids")
        book.progress = progress
        if preview_pages:  # Only set if we have at least one page
            book.preview_pages = preview_pages
            attributes.flag_modified(book, "preview_pages")

        all_done = len(completed) + len(failed_preds) == total

        if all_done:
            if len(failed_preds) == total:
                book.status = "failed"
                book.error_code = "ALL_PAGES_FAILED"
                book.error_message = "All page image generations failed"
                await self.db.flush()
                return {"status": "failed", "progress": 0, "completed_pages": [], "preview_pages": []}

            # Mark completed (allow partial failures gracefully)
            from datetime import datetime
            book.status = "completed"
            book.progress = 100
            book.completed_at = datetime.utcnow()
            generation_steps = dict(book.generation_steps or {})
            generation_steps["image_generation"] = "completed"
            generation_steps["pdf_generation"] = "completed"
            book.generation_steps = generation_steps
            book.current_step = None

            # Set cover image = first page
            if preview_pages:
                book.cover_image_url = preview_pages[0]["image_url"]

        await self.db.flush()

        return {
            "status": book.status,
            "progress": book.progress,
            "completed_pages": [info.get("page_number") for k, info in prediction_map.items() if info.get("status") == "succeeded"],
            "preview_pages": preview_pages,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_prompt(self, page: dict, child_name: str, child_gender: str) -> str:
        """
        Assemble the final Replicate prompt for a single page based on child's gender.
        
        Args:
            page: Page data containing prompt_male, prompt_female, or prompt_template
            child_name: Child's name to insert into prompt
            child_gender: Child's gender ('male', 'female', or 'other')
        
        Returns:
            Final prompt string with child name inserted
        """
        # Select the appropriate prompt based on gender
        if child_gender.lower() == "male" and "prompt_male" in page:
            base_template = page["prompt_male"]
        elif child_gender.lower() == "female" and "prompt_female" in page:
            base_template = page["prompt_female"]
        elif "prompt_template" in page:
            # Fallback to generic prompt_template for backwards compatibility or 'other' gender
            base_template = page["prompt_template"]
        else:
            # Fallback: use male prompt if nothing else is available
            base_template = page.get("prompt_male", page.get("prompt_female", ""))
        
        if not base_template:
            # If still no template, build from scene + background
            scene = page.get("scene", "")
            background = page.get("background", "")
            base_template = (
                f"children's storybook illustration, flat 2D pastel cartoon art style, {background}, "
                f"scene: {scene}, "
                f"a single 6-year-old human child named {child_name} standing in this scene, "
                f"same face and identity as reference photo, big round expressive eyes, rosy cheeks, warm soft smile, "
                f"full body visible, bold outlines, bright saturated cartoon colors, hand-drawn cartoon look, "
                f"vibrant pastel rainbow colors, soft glowing magical light, dreamy storybook atmosphere, "
                f"high quality children's book illustration, sharp bold lines, clean flat cartoon artwork"
            )
        
        # Replace child name placeholder
        prompt = base_template.replace("{child_name}", child_name)
        
        # Add "img" trigger word required by the model
        # Prepend it naturally as part of the prompt
        prompt = f"img, {prompt}"
        return prompt

    async def _create_prediction(self, prompt: str, image_url: str) -> str | None:
        """Call Replicate to start one img2img prediction. Returns prediction_id or None."""
        payload = {
            "version": settings.REPLICATE_MODEL_VERSION,
            "input": {
                "input_image": image_url,
                "prompt": prompt,
                "negative_prompt": (
                    "realistic, photograph, photorealistic, 3D render, blurry, low quality, "
                    "distorted face, deformed face, ugly, extra faces, multiple faces, "
                    "multiple persons, multiple characters, extra characters, duplicate characters, "
                    "crowd, group of people, three or more characters, background persons, "
                    "extra figures, extra bodies, clones, dark theme, scary, violent, "
                    "adult content, text, watermark, signature"
                ),
                "guidance_scale": 10,
            },
        }

        max_retries = settings.REPLICATE_MAX_RETRIES
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        f"{REPLICATE_API_BASE}/predictions",
                        json=payload,
                        headers=self._headers,
                    )

                    if response.status_code == 429:
                        # Use Retry-After header if present, otherwise exponential back-off
                        retry_after = int(response.headers.get("Retry-After", 0))
                        backoff = retry_after if retry_after > 0 else (2 ** attempt)
                        # Only log on first and last retry attempts to reduce noise
                        if attempt == 0 or attempt == max_retries - 1:
                            logger.warning(
                                "replicate_rate_limited",
                                attempt=attempt + 1,
                                max_retries=max_retries,
                                wait=backoff,
                            )
                        await asyncio.sleep(backoff)
                        continue

                    if response.status_code not in (200, 201):
                        logger.error(
                            "replicate_prediction_error",
                            status=response.status_code,
                            body=response.text[:500],
                        )
                        return None

                    data = response.json()
                    pred_id = data.get("id")
                    if pred_id:
                        logger.info("prediction_created", prediction_id=pred_id)
                    return pred_id

            except httpx.TimeoutException:
                backoff = 2 ** attempt
                # Only log timeouts on first and last attempt
                if attempt == 0 or attempt == max_retries - 1:
                    logger.warning("replicate_timeout", attempt=attempt + 1, max_retries=max_retries, wait=backoff)
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff)
            except Exception as exc:
                logger.error("replicate_unexpected_error", error=str(exc))
                return None

        return None

    async def _poll_prediction(self, client: httpx.AsyncClient, prediction_id: str) -> dict:
        """Fetch current status of one prediction from Replicate."""
        try:
            response = await client.get(
                f"{REPLICATE_API_BASE}/predictions/{prediction_id}",
                headers=self._headers,
            )
            if response.status_code == 200:
                return response.json()
            logger.warning("replicate_poll_error", prediction_id=prediction_id, status=response.status_code)
            return {}
        except Exception as exc:
            logger.error("replicate_poll_exception", prediction_id=prediction_id, error=str(exc))
            return {}

    async def _download_and_store(
        self,
        image_url: str,
        book_id: UUID,
        page_key: str,
        page_data: dict,
        child_name: str,
        child_gender: str,
    ) -> str | None:
        """
        Download generated image from Replicate CDN, add text overlay, and store in MinIO.
        
        Args:
            image_url: URL of the generated image from Replicate
            book_id: Book ID for storage path
            page_key: Page identifier key
            page_data: Page data containing story_line text
            child_name: Child's name for text personalization
            child_gender: Child's gender for pronoun personalization
        """
        try:
            # Download image from Replicate
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                image_bytes = response.content

            # Add text overlay if story_line is available
            story_line = page_data.get("story_line", "")
            if story_line:
                # Personalize the text
                personalized_text = self.text_overlay.personalize_text(
                    story_line, child_name, child_gender
                )
                # Add caption overlay
                image_bytes = self.text_overlay.add_caption(
                    image_bytes, personalized_text
                )
                logger.info(
                    "text_overlay_applied",
                    book_id=str(book_id),
                    page_key=page_key,
                    text_length=len(personalized_text),
                )

            # Upload to MinIO
            object_name = f"generated/books/story/{book_id}/pages/{page_key}.png"
            await self.storage.upload_file(
                file=io.BytesIO(image_bytes),
                object_name=object_name,
                content_type="image/png",
            )
            logger.info("page_image_stored", book_id=str(book_id), object_name=object_name)
            return object_name

        except Exception as exc:
            logger.error(
                "page_image_store_failed",
                book_id=str(book_id),
                page_key=page_key,
                error=str(exc),
            )
            return None

    async def _mark_failed(self, book_id: UUID, code: str, message: str) -> None:
        book = await self.repository.get_by_id(book_id)
        if book:
            from datetime import datetime
            book.status = "failed"
            book.error_code = code
            book.error_message = message
            book.failed_at = datetime.utcnow()
            await self.db.flush()
