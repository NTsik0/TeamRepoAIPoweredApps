"""Image prep before the model sees anything.

A phone photo is about 3000 px wide and several MB. The model reads a 1024 px JPEG just as
well, and every extra tile costs tokens. Re-saving also drops EXIF data (location, device).
"""
import io
import math

from PIL import Image, ImageOps


def downscale(image_bytes: bytes, max_side: int = 1024, quality: int = 85) -> bytes:
    """JPEG bytes with the longest side at most max_side. Never upscales, keeps the ratio,
    applies the photo's EXIF rotation, then writes a JPEG with no EXIF at all."""
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert("RGB")
    w, h = img.size
    scale = max_side / max(w, h)
    if scale < 1:
        img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=quality, optimize=True)
    return out.getvalue()


def approx_image_tokens(w: int, h: int, tile: int = 768, tokens_per_tile: int = 258) -> int:
    """Rough budget estimate only (about 258 tokens per 768 px tile for Gemini-family models).
    The real number is prompt_tokens in logs/usage.jsonl."""
    tiles = math.ceil(w / tile) * math.ceil(h / tile)
    return max(1, tiles) * tokens_per_tile
