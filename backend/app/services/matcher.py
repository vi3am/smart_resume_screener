from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Loaded once at import time — reused across every scoring call, not reloaded per request
model = SentenceTransformer("all-MiniLM-L6-v2")

def score_resume(job_description: str, resume_text: str) -> float:
    if not resume_text or not resume_text.strip():
        return 0.0

    embeddings = model.encode([job_description, resume_text])
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

    # Convert 0-1 similarity into a 0-100 score, easier for a recruiter to read
    return round(float(similarity) * 100, 2)