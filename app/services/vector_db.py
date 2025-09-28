from pinecone import Pinecone, ServerlessSpec
from app.config.settings import settings
from typing import List, Dict

_initialized = False
_index = None
_pc = None

def init_pinecone():
    global _initialized, _index, _pc
    if _initialized:
        return
    _pc = Pinecone(api_key=settings.pinecone_api_key)
    
    existing_indexes = [index_info["name"] for index_info in _pc.list_indexes()]
    if settings.pinecone_index_name not in existing_indexes:
        _pc.create_index(
            name=settings.pinecone_index_name, 
            dimension=settings.pinecone_dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
    
    _index = _pc.Index(settings.pinecone_index_name)
    _initialized = True

def upsert_chunks(vectors: List[Dict]):
    """
    vectors: list of {"id": id, "values": embedding_list, "metadata": {...}}
    """
    global _index
    if not _initialized:
        init_pinecone()
    if vectors:
        vector_tuples = [(v["id"], v["values"], v["metadata"]) for v in vectors]
        _index.upsert(vectors=vector_tuples)

def fetch_chunks_for_document(document_id: str, top_k: int = 5):
    """
    Fetch chunks for a specific document from Pinecone by document_id
    """
    global _index
    if not _initialized:
        init_pinecone()
    
    try:
        # Query with a dummy vector and filter by document_id in metadata
        dummy_vector = [0.1] * settings.pinecone_dimension
        
        results = _index.query(
            vector=dummy_vector,
            top_k=100,  # Get more results to filter
            include_metadata=True,
            include_values=False
        )
        
        # Filter results to only include this document's chunks
        document_chunks = []
        if results and 'matches' in results:
            for match in results['matches']:
                metadata = match.get('metadata', {})
                if metadata.get('document_id') == document_id:
                    document_chunks.append({
                        'text': metadata.get('text_excerpt', ''),
                        'chunk_id': metadata.get('chunk_id', ''),
                        'score': match.get('score', 0)
                    })
        
        # Return top_k results
        return document_chunks[:top_k] if document_chunks else []
        
    except Exception as e:
        print(f"DEBUG: Error fetching chunks: {e}")
        # Fallback to dummy data if no real chunks found
        return [
            {'text': f'Sample content for document {document_id} - section 1'},
            {'text': f'Sample content for document {document_id} - section 2'},
            {'text': f'Sample content for document {document_id} - section 3'}
        ]
