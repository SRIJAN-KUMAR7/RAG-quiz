import google.generativeai as genai
import json
import re
from app.config.settings import settings
from typing import List, Dict
import time

genai.configure(api_key=settings.gemini_api_key)

def list_available_models():
    """List all available models"""
    try:
        models = genai.list_models()
        available_models = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                available_models.append(model.name)
        print(f"Available models: {available_models}")
        return available_models
    except Exception as e:
        print(f"Error listing models: {e}")
        return []

def generate_questions(chunks_text: List[str], n_mcq: int = 5, n_match: int = 3, n_short: int = 5) -> List[Dict]:
    """
    Generate structured questions from document chunks using Gemini AI
    """
    try:
        # First, get available models
        available_models = list_available_models()
        
        # If no models available, return fallback
        if not available_models:
            print("DEBUG: No models available, using fallback")
            return create_fallback_questions(n_mcq, n_short, chunks_text)
        
        # Combine chunks into context, limiting length to avoid token limits
        context = "\n\n".join(chunks_text[:5])
        if len(context) > 4000:  # Limit context length
            context = context[:4000] + "..."
        
        print(f"DEBUG: Context length: {len(context)} characters")
        
        # Create structured prompt for better results
        prompt = f"""
Based on the following document content, generate exactly {n_mcq} multiple choice questions and {n_short} short answer questions.

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

Return only the JSON array with {n_mcq + n_short} questions total.
"""
        
        # Try available models
        for model_name in available_models:
            try:
                print(f"DEBUG: Trying model: {model_name}")
                model = genai.GenerativeModel(model_name)
                
                response = model.generate_content(prompt)
                
                if response.text:
                    print(f"DEBUG: Successfully got response from {model_name}")
                    break
                    
            except Exception as e:
                print(f"DEBUG: Model {model_name} failed: {e}")
                continue
        else:
            # If all models fail, return fallback questions
            print("DEBUG: All models failed, using fallback")
            return create_fallback_questions(n_mcq, n_short, chunks_text)
        
        print(f"DEBUG: LLM Raw Response: {response.text[:300]}...")
        
        # Clean and parse the response
        response_text = response.text.strip()
        
        # Try to extract JSON if it's wrapped in markdown or other text
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
        
        # Try to parse as JSON
        try:
            questions = json.loads(response_text)
            if isinstance(questions, list) and len(questions) > 0:
                # Validate and clean the questions
                validated_questions = validate_questions(questions, n_mcq, n_short)
                if validated_questions:
                    print(f"DEBUG: Successfully parsed {len(validated_questions)} questions")
                    return validated_questions
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON parsing failed: {e}")
        
        # Fallback: Parse text response
        print("DEBUG: Using text parsing fallback")
        return parse_text_to_questions(response.text, n_mcq, n_short)
        
    except Exception as e:
        print(f"DEBUG: Error in generate_questions: {e}")
        import traceback
        traceback.print_exc()
        return create_fallback_questions(n_mcq, n_short, chunks_text)

def validate_questions(questions: List[Dict], n_mcq: int, n_short: int) -> List[Dict]:
    """Validate and clean the questions from LLM response"""
    validated = []
    mcq_count = 0
    short_count = 0
    
    for q in questions:
        if not isinstance(q, dict):
            continue
            
        if not q.get('type') or not q.get('question'):
            continue
        
        question_type = q.get('type').lower()
        
        if question_type == 'mcq' and mcq_count < n_mcq:
            if q.get('options') and q.get('answer') and isinstance(q.get('options'), list):
                if len(q['options']) >= 2:
                    options = []
                    for i, option in enumerate(q['options'][:4]):
                        if not str(option).strip().startswith(('A)', 'B)', 'C)', 'D)')):
                            option = f"{chr(65+i)}) {str(option).strip()}"
                        options.append(str(option).strip())
                    
                    answer = str(q['answer']).strip()
                    if not any(answer.lower() in opt.lower() for opt in options):
                        answer = options[0]
                    
                    validated.append({
                        'type': 'mcq',
                        'question': str(q['question']).strip(),
                        'options': options,
                        'answer': answer
                    })
                    mcq_count += 1
        
        elif question_type in ['short', 'desc', 'descriptive'] and short_count < n_short:
            if q.get('answer'):
                validated.append({
                    'type': 'short',
                    'question': str(q['question']).strip(),
                    'answer': str(q['answer']).strip()
                })
                short_count += 1
    
    return validated

def parse_text_to_questions(text: str, n_mcq: int, n_short: int) -> List[Dict]:
    """Parse plain text LLM response into structured questions"""
    # Use the fallback for now since parsing is complex
    return create_fallback_questions(n_mcq, n_short, [])

def create_fallback_questions(n_mcq: int, n_short: int, chunks_text: List[str]) -> List[Dict]:
    """Create fallback questions when LLM fails"""
    questions = []
    
    # Extract some keywords from chunks for more relevant questions
    keywords = []
    if chunks_text:
        all_text = " ".join(chunks_text)
        words = re.findall(r'\b[A-Z][a-z]+\b', all_text)
        keywords = list(set(words))[:10]
    
    # Create MCQ questions
    for i in range(n_mcq):
        if keywords and i < len(keywords):
            keyword = keywords[i]
            question_text = f"What is the significance of '{keyword}' in the document?"
            options = [
                f"A) {keyword} is a key concept discussed in detail",
                f"B) {keyword} is mentioned briefly as background information",
                f"C) {keyword} is used as an example or case study",
                f"D) {keyword} is compared with other similar concepts"
            ]
        else:
            question_text = f"Based on the document content, what is the main point discussed in section {i+1}?"
            options = [
                f"A) Primary concept {i+1}",
                f"B) Secondary topic {i+1}",
                f"C) Supporting detail {i+1}",
                f"D) Related subject {i+1}"
            ]
        
        questions.append({
            "type": "mcq",
            "question": question_text,
            "options": options,
            "answer": options[0]
        })
    
    # Create short answer questions
    for i in range(n_short):
        if keywords and i < len(keywords):
            keyword = keywords[i]
            question_text = f"Explain the role of '{keyword}' as discussed in the document."
            answer = f"'{keyword}' plays an important role in the document's main theme."
        else:
            question_text = f"Describe the key concept {i+1} mentioned in this document."
            answer = f"Key concept {i+1} involves important aspects central to the document's discussion."
        
        questions.append({
            "type": "short",
            "question": question_text,
            "answer": answer
        })
    
    print(f"DEBUG: Created {len(questions)} fallback questions")
    return questions
