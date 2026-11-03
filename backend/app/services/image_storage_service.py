import io

from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

register_heif_opener()

# Content types are derived from file signatures, never from client-supplied headers.

HEIF_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"mif1", b"msf1", b"heif"}
# Formats browsers cannot reliably render; these are converted to JPEG on upload.
CONVERT_TYPES = {"image/heic", "image/tiff"}


def detect_image_type(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:2] == b"BM" and len(data) > 14:
        return "image/bmp"
    if data[:4] in (b"II*\x00", b"MM\x00*"):
        return "image/tiff"
    if data[4:8] == b"ftyp" and data[8:12] in HEIF_BRANDS:
        return "image/heic"
    return None


def normalize_image(data: bytes, content_type: str) -> tuple[bytes, str] | None:
    """Convert non-browser-friendly formats to JPEG. Returns None if the file can't be decoded."""
    if content_type not in CONVERT_TYPES:
        return data, content_type
    try:
        with Image.open(io.BytesIO(data)) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            out = io.BytesIO()
            img.save(out, format="JPEG", quality=90)
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        return None
    return out.getvalue(), "image/jpeg"
