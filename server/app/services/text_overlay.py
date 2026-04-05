"""Text Overlay Service for Adding Captions to Generated Images"""

import io
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

from app.common.logging import get_logger

logger = get_logger(__name__)


class TextOverlayService:
    """Service for adding text captions to storybook images"""

    # Font paths to try (in order of preference)
    FONT_PATHS = [
        "C:/Windows/Fonts/arialbd.ttf",  # Windows - Arial Bold
        "C:/Windows/Fonts/arial.ttf",     # Windows - Arial
        "C:/Windows/Fonts/calibrib.ttf",  # Windows - Calibri Bold
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
    ]

    FONT_SIZE = 44
    BAND_HEIGHT = 170
    PADDING = 80  # Horizontal padding for text
    LINE_SPACING = 8  # Space between lines
    STROKE_WIDTH = 2  # Outline width

    def __init__(self):
        """Initialize the text overlay service"""
        self.font = self._load_font()

    def _load_font(self) -> ImageFont.FreeTypeFont:
        """Load the best available font"""
        for font_path in self.FONT_PATHS:
            if Path(font_path).exists():
                try:
                    return ImageFont.truetype(font_path, self.FONT_SIZE)
                except Exception as exc:
                    logger.warning(f"Failed to load font {font_path}: {exc}")
                    continue

        # Fallback to default
        logger.warning("No custom fonts available, using default")
        try:
            return ImageFont.load_default(size=self.FONT_SIZE)
        except TypeError:
            # Older Pillow versions don't support size parameter
            return ImageFont.load_default()

    def _wrap_text(
        self, text: str, max_width: int, draw: ImageDraw.ImageDraw
    ) -> list[str]:
        """
        Wrap text to fit within max_width.
        Returns a list of lines.
        """
        words = text.split()
        lines = []
        current = ""

        for word in words:
            test = f"{current} {word}" if current else word
            bbox = draw.textbbox((0, 0), test, font=self.font)
            w = bbox[2] - bbox[0]

            if w <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines

    def add_caption(
        self,
        image_bytes: bytes,
        caption_text: str,
    ) -> bytes:
        """
        Add a caption below the image (extends canvas downward).

        Args:
            image_bytes: Original image as bytes
            caption_text: Text to display as caption

        Returns:
            Modified image with caption below as bytes (PNG format)
        """
        try:
            # Open original image
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            w, h = img.size

            # Create a temporary draw to calculate text dimensions
            temp_overlay = Image.new("RGBA", (w, self.BAND_HEIGHT), (0, 0, 0, 0))
            temp_draw = ImageDraw.Draw(temp_overlay)

            # Wrap text to fit
            max_text_width = w - self.PADDING
            lines = self._wrap_text(caption_text, max_text_width, temp_draw)

            # Calculate total text height
            total_text_h = sum(
                temp_draw.textbbox((0, 0), line, font=self.font)[3]
                - temp_draw.textbbox((0, 0), line, font=self.font)[1]
                + self.LINE_SPACING
                for line in lines
            )

            # Ensure band height is sufficient
            band_height = max(self.BAND_HEIGHT, total_text_h + 40)  # 40px top/bottom padding

            # Create new canvas with extended height
            new_height = h + band_height
            new_canvas = Image.new("RGB", (w, new_height), (0, 0, 0))

            # Paste original image at the top
            new_canvas.paste(img, (0, 0))

            # Create overlay for the caption band
            overlay = Image.new("RGBA", (w, new_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            # Draw solid dark band at bottom
            draw.rectangle(
                [(0, h), (w, new_height)],
                fill=(0, 0, 0, 255)  # Solid black band
            )

            # Start Y position (centered in band)
            y = h + (band_height - total_text_h) // 2

            # Draw each line
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=self.font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                x = (w - tw) / 2

                # Draw black stroke outline
                for dx, dy in [
                    (-self.STROKE_WIDTH, -self.STROKE_WIDTH),
                    (-self.STROKE_WIDTH, self.STROKE_WIDTH),
                    (self.STROKE_WIDTH, -self.STROKE_WIDTH),
                    (self.STROKE_WIDTH, self.STROKE_WIDTH),
                    (-self.STROKE_WIDTH, 0),
                    (self.STROKE_WIDTH, 0),
                    (0, -self.STROKE_WIDTH),
                    (0, self.STROKE_WIDTH),
                ]:
                    draw.text(
                        (x + dx, y + dy),
                        line,
                        fill=(0, 0, 0, 255),
                        font=self.font
                    )

                # Draw white text
                draw.text((x, y), line, fill=(255, 255, 255, 255), font=self.font)
                y += th + self.LINE_SPACING

            # Composite the overlay onto the canvas
            new_canvas = new_canvas.convert("RGBA")
            combined = Image.alpha_composite(new_canvas, overlay)

            # Convert to RGB and save to bytes
            output = io.BytesIO()
            combined.convert("RGB").save(output, format="PNG", quality=95)
            output.seek(0)

            logger.info(
                "text_caption_added_below_image",
                text_length=len(caption_text),
                original_size=(w, h),
                new_size=(w, new_height),
                num_lines=len(lines),
            )

            return output.read()

        except Exception as exc:
            logger.error(
                "text_overlay_failed",
                error=str(exc),
                caption=caption_text[:100],
            )
            # Return original image if overlay fails
            return image_bytes

    def personalize_text(
        self,
        story_line: str,
        child_name: str,
        child_gender: str,
    ) -> str:
        """
        Personalize story_line text with child's name and appropriate pronouns.

        Args:
            story_line: Original story line (uses "child", "they", "them", "their")
            child_name: Child's name
            child_gender: Child's gender ('male', 'female', 'other')

        Returns:
            Personalized story line
        """
        text = story_line

        # Replace "child" with child's name
        text = text.replace("child", child_name)
        text = text.replace("Child", child_name)

        # Determine pronouns based on gender
        if child_gender.lower() == "male":
            pronouns = {
                "they": "he",
                "They": "He",
                "them": "him",
                "Them": "Him",
                "their": "his",
                "Their": "His",
                "theirs": "his",
                "Theirs": "His",
            }
        elif child_gender.lower() == "female":
            pronouns = {
                "they": "she",
                "They": "She",
                "them": "her",
                "Them": "Her",
                "their": "her",
                "Their": "Her",
                "theirs": "hers",
                "Theirs": "Hers",
            }
        else:
            # Keep gender-neutral pronouns for 'other' or unspecified
            return text

        # Replace pronouns
        for neutral, gendered in pronouns.items():
            text = text.replace(f" {neutral} ", f" {gendered} ")
            text = text.replace(f" {neutral}.", f" {gendered}.")
            text = text.replace(f" {neutral},", f" {gendered},")

        return text
