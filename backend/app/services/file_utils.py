import os
import re
import unicodedata
import uuid

MAX_SLUG_LEN = 60
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def slugify(value: str) -> str:
    """Normalize any string into a safe, filesystem-friendly slug."""
    if not value:
        return ""

    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    value = re.sub(r"[\s_-]+", "_", value)
    return value[:MAX_SLUG_LEN].strip("_")


def safe_extension(original_filename: str) -> str:
    """Return a recognized extension; otherwise reject the upload."""
    ext = os.path.splitext(original_filename)[1].lower()
    if ext in ALLOWED_EXTENSIONS:
        return ext
    raise ValueError("Unsupported file type")


def build_stored_filename(parsed_name: str | None, original_filename: str) -> dict:
    """
    Build a safe on-disk name and a separate display value.
    """
    ext = safe_extension(original_filename)

    base_slug = slugify(parsed_name) if parsed_name else slugify(
        os.path.splitext(original_filename)[0]
    )
    if not base_slug:
        base_slug = "candidate"

    unique_suffix = uuid.uuid4().hex[:8]
    stored_filename = f"{base_slug}_{unique_suffix}{ext}"

    display_name = parsed_name.strip() if parsed_name else None
    return {
        "stored_filename": stored_filename,
        "display_name": display_name,
    }
