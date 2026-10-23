"""Explainable four-component CV scoring. Pure functions: no database, no network.

Used by the API and by the evaluation harness, so both measure the same code.
"""
import re
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from datetime import date

import numpy as np

from app.core.education import EDUCATION_RANK
from app.services.fields import (
    _EDU_HEADINGS, _EXP_HEADINGS, _OTHER_HEADINGS, _norm_heading,
    education_levels, years_of_experience,
)

Embedder = Callable[[list[str]], Sequence[Sequence[float]]]

DEFAULT_WEIGHTS = {"skills": 0.4, "experience": 0.2, "education": 0.1, "semantic": 0.3}
IN_PROGRESS_CREDIT = 70.0
SEMANTIC_LO, SEMANTIC_HI, SEMANTIC_TOP_K = 0.05, 0.60, 3
_HEADINGS = _EXP_HEADINGS | _EDU_HEADINGS | _OTHER_HEADINGS

# General-knowledge synonyms only. Do not add entries by reading test-posting CVs.
_ALIASES = {
    "javascript": ["js"],
    "postgresql": ["postgres"],
    "rest api": ["restful api", "restful apis"],
    "adobe photoshop": ["photoshop"],
    "adobe illustrator": ["illustrator"],
    "microsoft office": ["ms office", "microsoft word", "microsoft excel", "ms word", "ms excel"],
}


@dataclass
class ScoreResult:
    skills: float
    experience: float
    education: float
    semantic: float
    overall: float
    matched_skills: list[str]
    missing_skills: list[str]

    def as_dict(self) -> dict:
        return asdict(self)


def default_embed(texts: list[str]):
    from app.services.matcher import get_model
    return get_model().encode(texts, normalize_embeddings=True, show_progress_bar=False)


# ------------------------------------------------------------------- skills
def _norm(text: str) -> str:
    s = re.sub(r"[^a-z0-9+#.]+", " ", text.lower())
    s = re.sub(r"(?<![a-z0-9])\.|\.(?![a-z0-9])", " ", s)
    return " " + re.sub(r"\s+", " ", s).strip() + " "


def match_skills(required: Sequence[str], cv_text: str) -> tuple[list[str], list[str]]:
    haystack = _norm(cv_text)
    matched: list[str] = []
    missing: list[str] = []
    seen: set[str] = set()
    for skill in required:
        key = skill.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        forms: set[str] = set()
        for variant in {_norm(skill)} | {_norm(a) for a in _ALIASES.get(key, [])}:
            forms.add(variant)
            forms.add(variant[:-1] + "s ")  # simple plural
        (matched if any(f in haystack for f in forms) else missing).append(skill.strip())
    return matched, missing


def skills_score(matched: Sequence[str], missing: Sequence[str]) -> float:
    total = len(matched) + len(missing)
    return 100.0 if total == 0 else round(100 * len(matched) / total, 2)


# --------------------------------------------------------- experience, education
def experience_score(years: float, min_years: int) -> float:
    if min_years <= 0:
        return 100.0
    return round(100 * min(1.0, years / min_years), 2)


def education_score(completed: str | None, in_progress: str | None, min_level: str) -> float:
    if min_level not in EDUCATION_RANK:
        raise ValueError(f"unknown education level: {min_level!r}")
    need = EDUCATION_RANK[min_level]
    have = EDUCATION_RANK[completed] if completed else -1
    if have >= need:
        return 100.0
    linear = 100 * (have + 1) / (need + 1)
    if in_progress and EDUCATION_RANK[in_progress] >= need:
        return round(max(IN_PROGRESS_CREDIT, linear), 2)
    return round(linear, 2)


# ----------------------------------------------------------------- semantic
def split_sections(text: str, max_lines: int = 8, min_chars: int = 20) -> list[str]:
    """Cut a CV into section-sized chunks: at headings, and every max_lines lines."""
    chunks: list[str] = []
    current: list[str] = []

    def flush() -> None:
        for i in range(0, len(current), max_lines):
            block = " ".join(line.strip() for line in current[i:i + max_lines]).strip()
            if len(block) >= min_chars:
                chunks.append(block)
        current.clear()

    for line in text.splitlines():
        if not line.strip():
            continue
        if _norm_heading(line) in _HEADINGS:
            flush()
            continue
        current.append(line)
    flush()
    return chunks


def semantic_score(job_query: str, cv_text: str, embed: Embedder,
                k: int = SEMANTIC_TOP_K, lo: float = SEMANTIC_LO,
                hi: float = SEMANTIC_HI) -> float:
    chunks = split_sections(cv_text)
    if not chunks:
        return 0.0
    vecs = np.asarray(embed([job_query] + chunks), dtype=float)
    vecs = vecs / np.maximum(np.linalg.norm(vecs, axis=1, keepdims=True), 1e-12)
    sims = np.sort(vecs[1:] @ vecs[0])[::-1][:k]
    cos = float(sims.mean())
    return round(100 * min(1.0, max(0.0, (cos - lo) / (hi - lo))), 2)


# ------------------------------------------------------------------ overall
def _check_weights(weights: dict[str, float]) -> None:
    if set(weights) != set(DEFAULT_WEIGHTS):
        raise ValueError(f"weights must have exactly these keys: {sorted(DEFAULT_WEIGHTS)}")
    if any(w < 0 for w in weights.values()) or sum(weights.values()) <= 0:
        raise ValueError("weights must be non-negative and not all zero")


def score_cv(posting: dict, cv_text: str, *, fields: dict | None = None,
            weights: dict[str, float] | None = None, embed: Embedder | None = None,
            as_of: date | None = None) -> ScoreResult:
    weights = weights or DEFAULT_WEIGHTS
    _check_weights(weights)
    if fields is None:
        completed, in_progress = education_levels(cv_text)
        fields = {
            "years_experience": years_of_experience(cv_text, as_of),
            "education_level": completed,
            "education_in_progress": in_progress,
        }

    required = list(posting.get("required_skills") or [])
    matched, missing = match_skills(required, cv_text)
    parts = {
        "skills": skills_score(matched, missing),
        "experience": experience_score(fields.get("years_experience") or 0.0,
                                    posting.get("min_years_experience") or 0),
        "education": education_score(fields.get("education_level"),
                                    fields.get("education_in_progress"),
                                    posting.get("min_education_level") or "high_school"),
    }
    job_query = (f"{posting['title']}. {posting['description']} "
                f"Required skills: {', '.join(required)}")
    parts["semantic"] = semantic_score(job_query, cv_text, embed or default_embed)

    overall = sum(weights[k] * parts[k] for k in parts) / sum(weights.values())
    return ScoreResult(**parts, overall=round(overall, 2),
                    matched_skills=matched, missing_skills=missing)