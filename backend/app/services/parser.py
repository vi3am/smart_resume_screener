"""
Resume text extraction and field parsing.

Name extraction is inherently heuristic: general-purpose spaCy NER was never
trained on resume-specific text, so it regularly misidentifies technical terms,
institution names, and stylized headers as PERSON entities. The functions below
layer multiple targeted filters to catch the failure patterns discovered during
testing against ~15 real and template resumes. This is a documented, accepted
limitation — see the project's test report for the full list of known failure
categories (multi-column layout reordering, domain-vocabulary collisions,
letter-spaced/stylized header text breaking tokenization).
"""

import re

import pdfplumber
import docx
import spacy

nlp = spacy.load("en_core_web_sm")

# ---------------------------------------------------------------------------
# Contact-field patterns
# ---------------------------------------------------------------------------

EMAIL_PATTERN = r"[\w.+-]+@[\w-]+\.[\w.-]+"
PHONE_PATTERN = r"\+?\d[\d\s\-]{7,}\d"

# ---------------------------------------------------------------------------
# Skill keywords
# ---------------------------------------------------------------------------

COMMON_SKILLS = [
    # Technical
    "python", "java", "javascript", "react", "node.js", "sql", "postgresql",
    "docker", "aws", "machine learning", "data analysis", "html", "css",
    "fastapi", "django", "flask", "git", "excel", "power bi", "tableau",
    "matplotlib", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
    # Creative / media
    "photography", "videography", "voice-over", "video editing",
    "photo editing", "graphic design", "adobe photoshop", "adobe premiere",
    "illustrator", "after effects",
    # Soft skills
    "teamwork", "time management", "communication", "leadership",
    "problem solving", "critical thinking", "project management",
    "customer service", "public speaking",
]

# Tech/tool/framework terms that keep getting mistaken for person names.
# Living list — expect to keep extending this as new resumes surface new terms.
TECH_TERMS = {
    "jetpack compose", "kotlin", "flutter", "firebase", "langchain",
    "pinecone", "scikit-learn", "matplotlib", "fastapi", "django",
    "laravel", ".net", "c#", "tensorflow", "pytorch",
}

# ---------------------------------------------------------------------------
# Name-filtering vocabularies
# ---------------------------------------------------------------------------

PLACEHOLDER_NAME_PATTERN = re.compile(
    r"\b(lorem|ipsum|dolore|magna|aliqua|consectetur|adipiscing|elit|tempor|"
    r"incididunt|labore|eiusmod|company name|your degree|university name|"
    r"phone|email|contact)\b",
    re.IGNORECASE,
)

URL_DOMAIN_PATTERN = re.compile(
    r"(?:https?://|www\.)?[a-z0-9][a-z0-9.-]+\.[a-z]{2,}"
    r"(?:/[a-z0-9._~:/?#[\]@!$&'()*+,;=%-]*)?",
    re.IGNORECASE,
)

SOCIAL_HANDLE_PATTERN = re.compile(r"^@\w+")

NAME_STOP_WORDS = {
    "about", "me", "contact", "phone", "email", "address", "education",
    "experience", "reference", "language", "company", "company name",
    "university", "university name", "your degree", "job position",
}

RESUME_SECTION_LABELS = {
    "summary", "experience", "education", "skills", "profile", "objective",
    "contact", "projects", "certifications", "references", "work", "history",
    "languages", "interests", "detail", "details", "career",
}

INSTITUTION_TOKENS = {
    "university", "college", "institute", "academy", "school",
    "polytechnic", "faculty",
}

JOB_TITLE_TOKENS = {
    "accounting", "accountant", "assistant", "associate", "analyst",
    "administrator", "advisor", "consultant", "coordinator", "developer",
    "director", "engineer", "executive", "intern", "manager",
    "officer", "specialist", "supervisor", "lead", "representative",
    "designer", "architect", "scientist", "researcher", "teacher",
    "trainer", "sales", "marketing", "human", "resources",
}

JOB_TITLE_PHRASES = ("executive", "manager", "specialist", "analyst", "consultant")


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text(file_path: str) -> str:
    if file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif file_path.endswith(".docx"):
        d = docx.Document(file_path)
        return "\n".join(p.text for p in d.paragraphs)
    raise ValueError(f"Unsupported file type: {file_path}")


# ---------------------------------------------------------------------------
# Name-candidate filters
# ---------------------------------------------------------------------------

def _tokens(candidate: str) -> set[str]:
    cleaned = re.sub(r"[^a-z0-9\s]+", " ", candidate.lower())
    return set(re.findall(r"[a-z0-9]+", cleaned))


def looks_like_placeholder_name(candidate: str) -> bool:
    """Lorem-ipsum text, generic stop-words, or a candidate made up entirely
    of resume-section vocabulary (e.g. 'Summary Experience')."""
    if not candidate:
        return True

    cleaned_text = re.sub(r"[^a-z0-9\s]+", " ", candidate.lower())
    if PLACEHOLDER_NAME_PATTERN.search(cleaned_text):
        return True

    simple = re.sub(r"\s+", " ", cleaned_text).strip()
    if simple in NAME_STOP_WORDS:
        return True

    tokens = _tokens(candidate)
    if tokens and tokens.issubset(RESUME_SECTION_LABELS):
        return True

    return False


def looks_like_job_title(candidate: str) -> bool:
    """Rejects job-title/department fragments like 'Accounting Executive'."""
    cleaned = re.sub(r"[^a-z0-9\s]+", " ", candidate.lower())
    tokens = _tokens(candidate)

    if tokens.intersection(JOB_TITLE_TOKENS):
        return True

    if any(word in cleaned for word in JOB_TITLE_PHRASES):
        return True

    return False


def looks_like_institution(candidate: str) -> bool:
    """Rejects education-institution names like 'Wardiere University'."""
    return bool(_tokens(candidate).intersection(INSTITUTION_TOKENS))


def is_title_or_upper_case(candidate: str) -> bool:
    """Real names are Title Case ('John Smith') or ALL CAPS ('JOHN SMITH') —
    never fully lowercase, which usually signals a stray sentence fragment."""
    words = candidate.split()
    if not words:
        return False
    return all(w[0].isupper() for w in words if w[0].isalpha())


def contains_section_label(candidate: str) -> bool:
    """True if ANY word in the candidate overlaps a resume section label —
    catches entities where NER merged a real name with adjacent header text,
    e.g. 'LILA Career Summary'. Any overlap is enough to reject; a genuine
    name should never share a token with a section header."""
    return bool(_tokens(candidate) & RESUME_SECTION_LABELS)


def looks_like_real_name(candidate: str) -> bool:
    if not candidate:
        return False

    if looks_like_placeholder_name(candidate):
        return False

    if looks_like_job_title(candidate):
        return False

    if looks_like_institution(candidate):
        return False

    if URL_DOMAIN_PATTERN.search(candidate):
        return False

    if SOCIAL_HANDLE_PATTERN.match(candidate.strip()):
        return False

    if not is_title_or_upper_case(candidate):
        return False

    if len(candidate.split()) > 5:
        return False

    if candidate.lower() in COMMON_SKILLS:
        return False

    if candidate.lower() in TECH_TERMS:
        return False

    if re.search(EMAIL_PATTERN, candidate):
        return False

    if re.search(PHONE_PATTERN, candidate):
        return False

    if any(token.isdigit() for token in candidate.split()):
        return False

    if "\n" in candidate:
        return False

    if re.search(r"[\+\-\d]{7,}", candidate):
        return False

    if contains_section_label(candidate):
        return False

    return True


def strip_known_noise(candidate: str) -> str:
    """If a section-label word got merged into an entity span (e.g. NER
    returning 'LILA Career Summary'), strip the noise words out and see if
    what remains still looks like a plausible (partial) name."""
    words = candidate.split()
    cleaned_words = [w for w in words if w.lower() not in RESUME_SECTION_LABELS]
    return " ".join(cleaned_words).strip()




# ---------------------------------------------------------------------------
# Main parsing entry point
# ---------------------------------------------------------------------------

def _header_window(text: str, max_lines: int = 8) -> str:
    """First few lines of the document — respects word/line boundaries,
    unlike a raw character slice which can truncate mid-word."""
    lines = text.splitlines()
    return "\n".join(lines[:max_lines])


def parse_resume(text: str) -> dict:
    emails = re.findall(EMAIL_PATTERN, text)
    phones = re.findall(PHONE_PATTERN, text)

    text_lower = text.lower()
    found_skills = [skill for skill in COMMON_SKILLS if skill in text_lower]

    # Priority 1: resume convention — the name is almost always the first
    # non-empty line. This sidesteps spaCy's known weakness on all-caps
    # names entirely, and is more reliable than NER for well-ordered templates.
    name = None
    for line in text.splitlines():
        clean_line = line.strip()
        if not clean_line:
            continue
        if looks_like_real_name(clean_line):
            name = clean_line
        break  # only ever look at the very first non-empty line here

    # Priority 2: NER on the header window — for templates where the first
    # line is NOT the name (e.g. sidebar/contact info extracted before the
    # header due to column-ordering quirks).
    if not name:
        name = _find_name_in_window(_header_window(text))

    # Priority 3: NER on the full document, as a last resort.
    if not name:
        name = _find_name_in_window(text)

    return {
        "name": name,
        "email": emails[0] if emails else None,
        "phone": phones[0].strip() if phones else None,
        "skills": found_skills,
    }

def _find_name_in_window(window_text: str) -> str | None:
    doc = nlp(window_text)
    candidates: list[tuple[int, str]] = []

    for ent in doc.ents:
        if ent.label_ != "PERSON":
            continue
        raw_candidate = ent.text.strip()

        if looks_like_real_name(raw_candidate):
            candidates.append((ent.start_char, raw_candidate))
            continue

        repaired = strip_known_noise(raw_candidate)
        if repaired and repaired != raw_candidate and looks_like_real_name(repaired):
            candidates.append((ent.start_char, repaired))

    candidates.sort(key=lambda c: c[0])
    return candidates[0][1] if candidates else None