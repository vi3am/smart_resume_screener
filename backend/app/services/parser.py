import pdfplumber
import docx
import re
import spacy

nlp = spacy.load("en_core_web_sm")

EMAIL_PATTERN = r"[\w.+-]+@[\w-]+\.[\w.-]+"
PHONE_PATTERN = r"\+?\d[\d\s\-]{7,}\d"

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


def extract_text(file_path: str) -> str:
    if file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif file_path.endswith(".docx"):
        d = docx.Document(file_path)
        return "\n".join(p.text for p in d.paragraphs)
    raise ValueError(f"Unsupported file type: {file_path}")




def parse_resume(text: str) -> dict:
    emails = re.findall(EMAIL_PATTERN, text)
    phones = re.findall(PHONE_PATTERN, text)

    text_lower = text.lower()
    found_skills = [skill for skill in COMMON_SKILLS if skill in text_lower]

    header_text = text[:300]
    header_doc = nlp(header_text)
    
    candidate_names = [
        ent.text for ent in header_doc.ents
        if ent.label_ == "PERSON" and ent.text.lower() not in COMMON_SKILLS
    ]

    name = candidate_names[0] if candidate_names else None
    


    if not name:
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), None)
        if first_line and len(first_line.split()) <= 5:  # avoid grabbing a long sentence
            name = first_line

    return {
        "name": name,
        "email": emails[0] if emails else None,
        "phone": phones[0].strip() if phones else None,
        "skills": found_skills,
    }