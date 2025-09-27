import google.generativeai as genai
from app.config.settings import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

def generate_questions(context: str, existing: list[str] = None) -> str:
    prompt = f"""From the following content generate 5 MCQs and 5 descriptive questions.
Avoid duplicates: {existing}.
Content:
{context}"""
    model = genai.GenerativeModel('gemini-pro')
    resp = model.generate_content(prompt)
    return resp.text
