# from typing import List
# from app.config.settings import settings
# import google.generativeai as genai  # <-- correct import

# # configure Gemini once
# genai.configure(api_key=settings.gemini_api_key)

# def get_embeddings(texts: List[str]) -> List[List[float]]:
#     """
#     Generate embeddings for a list of texts using Gemini API.
#     """
#     if not texts:
#         return []

#     # Gemini embeddings API call
#     response = genai.embed_content(
#         model="models/embedding-001",  # or "text-embedding-004"
#         content=texts
#     )

#     # response['embedding'] is the vector for one text
#     # but when you pass a list of texts you get .embeddings for each input
#     # (current SDK returns .embedding for a single, or .embeddings for batch)
#     if hasattr(response, "embeddings"):
#         return [item["embedding"] for item in response.embeddings]
#     elif "embedding" in response:
#         # single text
#         return [response["embedding"]]
#     else:
#         raise RuntimeError(f"Unexpected embedding response: {response}")


#alternative :can use oLLama
#fake embeddings just for implementing the RAG

from typing import List
import numpy as np  

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Fake embeddings for testing without calling Gemini.
    Generates random 768-dim vectors for each text.
    """
    if not texts:
        return []

    dim = 1024 
    return [np.random.rand(dim).tolist() for _ in texts]
