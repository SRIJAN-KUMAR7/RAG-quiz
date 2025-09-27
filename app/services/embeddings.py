from typing import List
from app.config.settings import settings
import google.generativeai as genai

# Configure Gemini once
genai.configure(api_key=settings.gemini_api_key)
# to be corrected from here
def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using Gemini API.
    """
    if not texts:
        return []

    # Gemini embeddings API call
    response = genai.embeddings.create(
        model="textembedding-gecko-001",
        input=texts
    )
    embeddings = [item["embedding"] for item in response["data"]]

    return embeddings
