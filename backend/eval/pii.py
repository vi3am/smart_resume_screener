"""Detect and redact personal data in CV text. Used by the dataset tools only."""
import re
from collections.abc import Iterable

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
URL_RE = re.compile(
    r"(?i)(?:https?://\S+|www\.\S+"
    r"|\b(?:github|gitlab|linkedin|facebook|instagram|behance)\.com/\S*|\bt\.me/\S*)"
)
HANDLE_RE = re.compile(r"(?<![\w@])@[A-Za-z0-9_.]{3,}")
# 8-15 digits with single separators only (never a newline)
PHONE_RE = re.compile(r"(?<!\d)\+?\d(?:[ \t().-]?\d){7,14}(?!\d)")
YEAR_RANGE_RE = re.compile(r"(?:19|20)\d{2}\s*[-–/]?\s*(?:19|20)\d{2}")


def _is_year_range(text: str) -> bool:
    return bool(YEAR_RANGE_RE.fullmatch(text.strip()))


def find_pii(text: str) -> list[tuple[str, str]]:
    hits = [("email", m.group(0)) for m in EMAIL_RE.finditer(text)]
    hits += [("url", m.group(0)) for m in URL_RE.finditer(text)]
    hits += [("handle", m.group(0)) for m in HANDLE_RE.finditer(text)]
    hits += [
        ("phone", m.group(0))
        for m in PHONE_RE.finditer(text)
        if not _is_year_range(m.group(0))
    ]
    return hits


def redact(text: str, names: Iterable[str] = ()) -> str:
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = URL_RE.sub("[URL]", text)
    text = HANDLE_RE.sub("[HANDLE]", text)
    text = PHONE_RE.sub(
        lambda m: m.group(0) if _is_year_range(m.group(0)) else "[PHONE]", text
    )
    for name in names:
        full = r"\s+".join(re.escape(part) for part in name.split())
        text = re.sub(rf"\b{full}\b", "[NAME]", text, flags=re.IGNORECASE)
        for part in name.split():
            if len(part) >= 4:  # short parts like "But" would hit ordinary words
                text = re.sub(rf"\b{re.escape(part)}\b", "[NAME]", text, flags=re.IGNORECASE)
    return text