import pinecone
from app.config.settings import settings
from typing import List, Dict

_initialized = False
_index = None

def init_pinecone():
    global _initialized, _index
    if _initialized:
        return
    pinecone.init(api_key=settings.pinecone_api_key, environment=settings.pinecone_environment)
    # create index if not exists
    if settings.pinecone_index_name not in pinecone.list_indexes():
        pinecone.create_index(name=settings.pinecone_index_name, dimension=settings.pinecone_dimension, metric="cosine")
    _index = pinecone.Index(settings.pinecone_index_name)
    _initialized = True

def upsert_chunks(vectors: List[Dict]):
    """
    vectors: list of {"id": id, "values": embedding_list, "metadata": {...}}
    """
    global _index
    if not _initialized:
        init_pinecone()
    if vectors:
        # Pinecone expects a list of tuples or dicts depending on version
        _index.upsert(vectors=vectors)

def fetch_chunks_for_document(document_id: str, top_k: int = 5):
    """
    Example metadata filter query - requires that you set metadata 'document_id' on upsert.
    Returns metadata from matches.
    """
    global _index
    if not _initialized:
        init_pinecone()
    # Simple scan: filter by metadata
    # NOTE: Pinecone querying by metadata depends on version; for simplicity we do a vector-less filter via query with an all-zero vector (not ideal).
    # In your real code, store chunk ids in Postgres and use IDs or store namespace per document.
    return []  # implement as needed for retrieval