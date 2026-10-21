from pathlib import Path
from uuid import uuid4

from app.core.config import settings

# Content types are derived from file signatures, never from client-supplied headers.
_EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def detect_image_type(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


class LocalStorage:
    """Stores image bytes on local disk. Swap for S3/MinIO by keeping this interface."""

    def __init__(self, root: str | None = None) -> None:
        self.root = Path(root or settings.upload_dir).resolve()

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root not in path.parents:
            raise ValueError("Invalid storage key")
        return path

    def save(self, data: bytes, content_type: str) -> str:
        key = f"{uuid4().hex}{_EXTENSIONS[content_type]}"
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(key).write_bytes(data)
        return key

    def path(self, key: str) -> Path:
        return self._path(key)

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)


storage = LocalStorage()
