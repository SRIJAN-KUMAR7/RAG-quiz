def chunk_text(text: str, chunk_size: int = 800, overlap: int = 200):
    tokens = text.split()
    step = max(1, chunk_size - overlap)
    for i in range(0, len(tokens), step):
        yield " ".join(tokens[i:i + chunk_size])