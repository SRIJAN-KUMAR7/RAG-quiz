import pdfplumber
from pathlib import Path
from typing import List

def extract_text_pages(pdf_path: str) -> List[str]:
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for p in pdf.pages:
            pages.append(p.extract_text() or "")
    return pages

def extract_full_text(pdf_path: str) -> str:
    return "\n".join(extract_text_pages(pdf_path))
