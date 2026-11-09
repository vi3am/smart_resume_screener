"""Detect scanned (image-only) PDFs. There is no OCR in this project, so they are rejected."""
import re

MIN_TOTAL_CHARS = 100      # fewer visible characters than this in the whole file: scanned
MIN_CHARS_PER_PAGE = 30    # fewer than this on average per page: scanned
SCANNED_MESSAGE = (
    "This PDF looks scanned (no selectable text). Scanned files are not supported; "
    "upload a text-based PDF or a DOCX."
)


class ScannedPdfError(ValueError):
    """Raised when a PDF has pages but (almost) no extractable text."""


def is_scanned(page_texts: list[str]) -> bool:
    if not page_texts:
        return True
    visible = len(re.sub(r"\s+", "", "".join(page_texts)))
    return visible < MIN_TOTAL_CHARS or visible / len(page_texts) < MIN_CHARS_PER_PAGE