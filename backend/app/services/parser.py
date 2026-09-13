import re

import pdfplumber
import docx
import spacy

nlp = spacy.load("en_core_web_sm")

EMAIL_PATTERN = r"[\w.+-]+@[\w-]+\.[\w.-]+"
PHONE_PATTERN = r"\+?\d[\d\s\-]{7,}\d"

PLACEHOLDER_NAME_PATTERN = re.compile(
    r"\b(lorem|ipsum|dolore|magna|aliqua|consectetur|adipiscing|elit|tempor|incididunt|labore|eiusmod|company name|your degree|university name|phone|email|contact)\b",
    re.IGNORECASE,
)

URL_DOMAIN_PATTERN = re.compile(
    r"(?:https?://|www\.)?[a-z0-9][a-z0-9.-]+\.[a-z]{2,}(?:/[a-z0-9._~:/?#[\]@!$&'()*+,;=%-]*)?",
    re.IGNORECASE,
)

NAME_STOP_WORDS = {
    "about", "me", "contact", "phone", "email", "address", "education",
    "experience", "reference", "language", "company", "company name",
    "university", "university name", "your degree", "job position",
}

RESUME_SECTION_LABELS = {
    "summary", "experience", "education", "skills", "profile", "objective",
    "contact", "projects", "certifications", "references", "work", "history",
    "languages", "interests", "detail", "details",
}

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

JOB_TITLE_TOKENS = {
    "accounting", "accountant", "assistant", "associate", "analyst",
    "administrator", "advisor", "consultant", "coordinator", "developer",
    "director", "engineer", "executive", "intern", "manager",
    "officer", "specialist", "supervisor", "lead", "representative",
    "designer", "architect", "scientist", "researcher", "teacher",
    "trainer", "executive", "sales", "marketing", "human", "resources",
}


def looks_like_job_title(candidate: str) -> bool:
    
    cleaned = re.sub(r"[^a-z0-9\s]+", " ", candidate.lower())
    tokens = set(re.findall(r"[a-z0-9]+", cleaned))

    # Reject common job-title or department-title fragments that are not
    # plausible person-name inputs. This prevents top-line headline items like
    # "Accounting Executive" from being recorded as the candidate name.
    if tokens.intersection(JOB_TITLE_TOKENS):
        return True

    # Also reject natural-language title phrases containing role words but no
    # real alphabetic person-name evidence (e.g. "Senior Project Manager").
    if any(word in cleaned for word in ("executive", "manager", "specialist", "analyst", "consultant")):
        return True

    return False


def extract_text(file_path: str) -> str:
    if file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif file_path.endswith(".docx"):
        d = docx.Document(file_path)
        return "\n".join(p.text for p in d.paragraphs)
    raise ValueError(f"Unsupported file type: {file_path}")




def looks_like_placeholder_name(candidate: str) -> bool:
    if not candidate:
        return True

    cleaned = re.sub(r"[^a-z0-9\s]+", " ", candidate.lower())
    if PLACEHOLDER_NAME_PATTERN.search(cleaned):
        return True

    simple = re.sub(r"\s+", " ", cleaned).strip()
    if simple in NAME_STOP_WORDS:
        return True

    tokens = set(re.findall(r"[a-z0-9]+", cleaned))
    if tokens and tokens.issubset(RESUME_SECTION_LABELS):
        return True

    return False


def looks_like_real_name(candidate: str) -> bool:
    if not candidate or looks_like_placeholder_name(candidate):
        return False

    if looks_like_job_title(candidate):
        return False

    if URL_DOMAIN_PATTERN.search(candidate):
        return False

    if len(candidate.split()) > 5:
        return False

    if candidate.lower() in COMMON_SKILLS:
        return False

    if re.search(EMAIL_PATTERN, candidate):
        return False

    if re.search(PHONE_PATTERN, candidate):
        return False

    if any(token.isdigit() for token in candidate.split()):
        return False

    if "\n" in candidate:
        return False

    # Reject sentence-shaped or template fragments such as:
    # "laboris +123-456-7890" or similar mixed contact-artifact output.
    if re.search(r"[\+\-\d]{7,}", candidate):
        return False

    cleaned = re.sub(r"[^a-z0-9\s]+", " ", candidate.lower())
    tokens = set(re.findall(r"[a-z0-9]+", cleaned))

    # Reject pure resume-section header fragments such as:
    # "SUMMARY EXPERIENCE" or "SKILLS EDUCATION".
    if tokens and tokens.issubset(RESUME_SECTION_LABELS):
        return False

    return True


def parse_resume(text: str) -> dict:
    emails = re.findall(EMAIL_PATTERN, text)
    phones = re.findall(PHONE_PATTERN, text)

    text_lower = text.lower()
    found_skills = [skill for skill in COMMON_SKILLS if skill in text_lower]

    header_text = text[:300]
    header_doc = nlp(header_text)

    candidate_names = []
    for ent in header_doc.ents:
        if ent.label_ != "PERSON":
            continue
        candidate = ent.text.strip()
        if looks_like_real_name(candidate):
            candidate_names.append(candidate)

    name = candidate_names[0] if candidate_names else None

    if not name:
        # Prefer the first real top-of-file non-empty line that looks like a person name.
        for line in text.splitlines():
            clean_line = line.strip()
            if not clean_line:
                continue
            if looks_like_real_name(clean_line):
                name = clean_line
                break

    return {
        "name": name,
        "email": emails[0] if emails else None,
        "phone": phones[0].strip() if phones else None,
        "skills": found_skills,
    }