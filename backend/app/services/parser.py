import pdfplumber
import docx

def extract_text(file_path: str) -> str:
    if file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif file_path.endswith(".docx"):
        d = docx.Document(file_path)
        return "\n".join(p.text for p in d.paragraphs)
    raise ValueError(f"Unsupported file type: {file_path}")