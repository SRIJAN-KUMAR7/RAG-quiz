import google.generativeai as genai
import json, re, time, math
from typing import List, Dict
from app.config.settings import settings

genai.configure(api_key=settings.gemini_api_key)

# -------------------------------------------------
# tunables – change these if you hit limits again
# -------------------------------------------------
CHUNK_MAX_TOKENS   = 9_500          # stay safely below 10 k
USE_FLASH          = True           # 1 M context window vs 125 k
COMPRESS_FIRST     = False          # extra summarisation step
TOKENS_PER_CHAR    = 0.25           # ¼ token per char is conservative
# -------------------------------------------------

# ---------- tiny helpers ----------
def _count_tokens(text: str) -> int:
    """Cheap local estimate; falls back to real API if you want."""
    return math.ceil(len(text) * TOKENS_PER_CHAR)

def _truncate_to_budget(text: str, budget: int) -> str:
    """Truncate at sentence boundary under token budget."""
    if _count_tokens(text) <= budget:
        return text
    chars_budget = int(budget / TOKENS_PER_CHAR)
    cut = text[:chars_budget]
    # last sentence end
    sent_end = max(cut.rfind('.'), cut.rfind('!'), cut.rfind('?'))
    return text[:sent_end + 1] if sent_end > chars_budget * 0.8 else cut

def _choose_model():
    """Return model name that respects USE_FLASH flag."""
    return "gemini-1.5-flash" if USE_FLASH else "gemini-1.5-pro"

# ---------- public API ----------
def generate_questions(
    chunks_text: List[str],
    n_mcq: int = 5,
    n_match: int = 3,      # kept for compat, not used
    n_short: int = 5
) -> List[Dict]:
    """
    Generate questions from vector-db chunks without ever exceeding
    the free-tier token window (125 k for Pro, 1 M for Flash).
    """
    if not chunks_text:
        return create_fallback_questions(n_mcq, n_short, [])

    # 1. optional compression pass ---------------------------------
    if COMPRESS_FIRST:
        summary = _summarise_chunks(chunks_text)
        chunks_text = [summary]

    # 2. distribute question quota across chunks ------------------
    num_chunks = len(chunks_text)
    mcq_per_chunk, mcq_rem = divmod(n_mcq, num_chunks)
    short_per_chunk, short_rem = divmod(n_short, num_chunks)

    all_questions = []
    for idx, chunk in enumerate(chunks_text):
        this_mcq = mcq_per_chunk + (1 if idx < mcq_rem else 0)
        this_short = short_per_chunk + (1 if idx < short_rem else 0)
        if this_mcq == this_short == 0:
            continue

        # 3. truncate chunk to token budget -----------------------
        context = _truncate_to_budget(chunk, CHUNK_MAX_TOKENS)

        # 4. build prompt -----------------------------------------
        prompt = f"""
Based on the following document content, generate exactly {this_mcq} multiple choice questions and {this_short} short answer questions.
Return your response as a valid JSON array only. No other text.
Format each question exactly like this:
For Multiple Choice Questions:
{{
  "type": "mcq",
  "question": "Clear question text ending with ?",
  "options": ["A) First option", "B) Second option", "C) Third option", "D) Fourth option"],
  "answer": "A) First option"
}}
For Short Answer Questions:
{{
  "type": "short",
  "question": "Clear question text ending with ?",
  "answer": "Concise but complete answer"
}}
Document Content:
{context}
Return only the JSON array with {this_mcq + this_short} questions total.
"""

        # 5. call model with retry --------------------------------
        raw = _call_model_with_retry(prompt)
        if raw:
            parsed = _safe_parse_json_array(raw)
            all_questions.extend(parsed)

    # 6. final validation -----------------------------------------
    validated = validate_questions(all_questions, n_mcq, n_short)
    if not validated:
        validated = create_fallback_questions(n_mcq, n_short, chunks_text)
    return validated

# ---------- internal LLM caller ----------
def _call_model_with_retry(prompt: str, max_retry: int = 3) -> str:
    model_name = _choose_model()
    model = genai.GenerativeModel(model_name)
    for attempt in range(1, max_retry + 1):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            if "429" in str(e):
                wait = 5 * (2 ** (attempt - 1))
                time.sleep(wait)
            else:
                break
    return ""

# ---------- json sanitiser ----------
def _safe_parse_json_array(text: str) -> List[Dict]:
    m = re.search(r'\[.*\]', text, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []

# ---------- optional summariser ----------
def _summarise_chunks(chunks: List[str]) -> str:
    """One-shot summary of all chunks; keeps us under token limit."""
    merged = "\n".join(chunks)
    prompt = (
        "Summarise the following text in 5–6 concise sentences:\n\n" + merged
    )
    summary = _call_model_with_retry(prompt)
    return summary or merged[:4000]  # fallback

# ---------- your unchanged helpers ----------
def list_available_models():
    try:
        return [m.name for m in genai.list_models()
                if 'generateContent' in m.supported_generation_methods]
    except Exception:
        return []

def validate_questions(questions: List[Dict], n_mcq: int, n_short: int) -> List[Dict]:
    # (your original code – no changes)
    validated = []
    mcq_count = short_count = 0
    for q in questions:
        if not isinstance(q, dict):
            continue
        q_type = q.get("type", "").lower()
        if q_type == "mcq" and mcq_count < n_mcq:
            opts = [str(o).strip() for o in q.get("options", [])][:4]
            if len(opts) >= 2:
                for i, o in enumerate(opts):
                    if not re.match(r"^[A-D]\)", o):
                        opts[i] = f"{chr(65+i)}) {o}"
                ans = str(q.get("answer", opts[0])).strip()
                if not any(ans.lower() in o.lower() for o in opts):
                    ans = opts[0]
                validated.append({
                    "type": "mcq",
                    "question": str(q["question"]).strip(),
                    "options": opts,
                    "answer": ans
                })
                mcq_count += 1
        elif q_type in {"short", "desc", "descriptive"} and short_count < n_short:
            if q.get("answer"):
                validated.append({
                    "type": "short",
                    "question": str(q["question"]).strip(),
                    "answer": str(q["answer"]).strip()
                })
                short_count += 1
    return validated

def create_fallback_questions(n_mcq: int, n_short: int, chunks_text: List[str]) -> List[Dict]:
    # (your original code – no changes)
    questions = []
    keywords = []
    if chunks_text:
        all_text = " ".join(chunks_text)
        words = re.findall(r'\b[A-Z][a-z]+\b', all_text)
        keywords = list(set(words))[:10]
    for i in range(n_mcq):
        if i < len(keywords):
            kw = keywords[i]
            q = f"What is the significance of '{kw}' in the document?"
            opts = [
                f"A) {kw} is a key concept discussed in detail",
                f"B) {kw} is mentioned briefly as background information",
                f"C) {kw} is used as an example or case study",
                f"D) {kw} is compared with other similar concepts"
            ]
        else:
            q = f"What is the main point discussed in section {i+1}?"
            opts = [f"{chr(65 + j)}) Option {j + 1}" for j in range(4)]
        questions.append({"type": "mcq", "question": q, "options": opts, "answer": opts[0]})
    for i in range(n_short):
        if i < len(keywords):
            kw = keywords[i]
            q = f"Explain the role of '{kw}' as discussed in the document."
            a = f"'{kw}' plays an important role in the document's main theme."
        else:
            q = f"Describe key concept {i + 1} mentioned in this document."
            a = f"Key concept {i + 1} is central to the document's discussion."
        questions.append({"type": "short", "question": q, "answer": a})
    return questions
