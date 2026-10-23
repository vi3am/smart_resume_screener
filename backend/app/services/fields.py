"""Years-of-experience and education-level extraction from CV text. Pure functions."""
import re
from datetime import date

from app.core.education import EDUCATION_RANK

# ---------------------------------------------------------------- experience
_MON = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?"
_RANGE_RE = re.compile(
    r"(?:\b(?P<m1>" + _MON + r")\s+)?(?P<y1>(?:19|20)\d{2})\s*(?:-|–|—|to)\s*"
    r"(?:\b(?P<m2>" + _MON + r")\s+)?(?P<y2>(?:19|20)\d{2}|present|current|now|ongoing)\b",
    re.IGNORECASE,
)
_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}

_EXP_HEADINGS = {
    "experience", "work experience", "professional experience", "employment",
    "employment history", "work history", "career history", "career summary",
    "internship", "internships",
}
_EDU_HEADINGS = {"education", "educational background", "academic history", "academic background"}
_OTHER_HEADINGS = {
    "skills", "key skills", "core skills", "technical skills", "projects", "academic projects",
    "certifications", "training", "training & certifications", "training and certifications",
    "languages", "references", "reference", "summary", "professional summary", "profile",
    "about me", "interests", "achievements", "awards", "awards and certification", "contact",
    "volunteer experience", "volunteer experiences",
}
_EDU_WORDS = re.compile(
    r"university|college|school|institute|academy|bachelor|master|diploma|degree|baccalaureate",
    re.IGNORECASE,
)


def _norm_heading(line: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z&' ]", "", line.lower())).strip()


def _experience_lines(lines: list[str]) -> list[str]:
    section, has_heading, has_exp = None, False, False
    tagged: list[tuple[str | None, str]] = []
    for line in lines:
        h = _norm_heading(line)
        if h in _EXP_HEADINGS:
            section, has_heading, has_exp = "exp", True, True
        elif h in _EDU_HEADINGS:
            section, has_heading = "edu", True
        elif h in _OTHER_HEADINGS:
            section, has_heading = "other", True
        else:
            tagged.append((section, line))
    if has_exp:
        return [line for sec, line in tagged if sec == "exp"]
    if not has_heading:  # a CV with no headings at all: use every non-education line
        return [line for _, line in tagged if not _EDU_WORDS.search(line)]
    return []


def _months(year: int, month: str | None) -> int:
    return year * 12 + (_MONTHS[month[:3].lower()] if month else 1)


def years_of_experience(text: str, as_of: date | None = None) -> float:
    """Total years covered by date ranges in the experience section."""
    as_of = as_of or date.today()
    now = as_of.year * 12 + as_of.month
    spans: list[list[int]] = []
    for line in _experience_lines(text.splitlines()):
        for m in _RANGE_RE.finditer(line):
            start = _months(int(m["y1"]), m["m1"])
            end_raw = m["y2"].lower()
            end = now if not end_raw.isdigit() else _months(int(end_raw), m["m2"])
            if start >= now:  # starts in the future (template placeholder dates)
                continue
            end = min(end, now)
            if end > start:
                spans.append([start, end])
    spans.sort()
    merged: list[list[int]] = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return round(sum(e - s for s, e in merged) / 12, 1)


# ----------------------------------------------------------------- education
_PATTERNS = [
    ("phd", re.compile(r"(?i:\bph\.?\s?d\b|\bdoctorate\b|\bdoctoral\b)")),
    ("master", re.compile(
        r"(?i:\bmaster(?:'s|’s|s)?\s+(?:degree|of|in)\b)|\bM\.?Sc\b|\bMBA\b|\bM\.?Ed\b|\bM\.?Eng\b")),
    ("bachelor", re.compile(
        r"(?i:\bbachelor(?:'s|’s|s)?\b)|\bB\.?A\.?\b|\bB\.?Sc\b|\bB\.?Ed\b|\bB\.?Eng\b")),
    ("associate", re.compile(
        r"(?i:\bassociate(?:'s|’s)?\s+(?:degree|of|in)\b|\bhigher national diploma\b)|\bHND\b")),
    ("high_school", re.compile(r"(?i:\bhigh\s*school\b|\bbaccalaureate\b|\bsecondary school\b)")),
]
_STANDALONE = {"master": "master", "masters": "master",
            "bachelor": "bachelor", "bachelors": "bachelor", "phd": "phd"}
_PROGRESS_RE = re.compile(r"\b(?:present|in progress|expected|currently|ongoing)\b", re.IGNORECASE)


def _levels_in_line(line: str) -> list[str]:
    found = [level for level, rx in _PATTERNS if rx.search(line)]
    standalone = _STANDALONE.get(re.sub(r"[^a-z']", "", line.lower()))
    if standalone:
        found.append(standalone)
    return found


def _higher(current: str | None, new: str) -> str:
    return new if current is None or EDUCATION_RANK[new] > EDUCATION_RANK[current] else current


def education_levels(text: str) -> tuple[str | None, str | None]:
    """Return (highest completed level, highest in-progress level)."""
    lines = text.splitlines()
    completed = in_progress = None
    for i, line in enumerate(lines):
        levels = _levels_in_line(line)
        if not levels:
            continue
        in_prog = False
        for j in range(i, min(i + 3, len(lines))):
            if j > i and _levels_in_line(lines[j]):
                break  # the next degree starts here; its dates belong to it
            if _PROGRESS_RE.search(lines[j]):
                in_prog = True
                break
        for level in levels:
            if in_prog:
                in_progress = _higher(in_progress, level)
            else:
                completed = _higher(completed, level)
    return completed, in_progress