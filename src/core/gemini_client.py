import google.generativeai as genai
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential
from src.config import GOOGLE_API_KEY, GEMINI_MODEL, EMBEDDING_MODEL, MEDICAL_GRAPH_PROMPT

genai.configure(api_key=GOOGLE_API_KEY)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def gemini_llm_func(prompt, system_prompt=None, history_messages=[], **kwargs):
    model = genai.GenerativeModel(GEMINI_MODEL)
    
    # Sandwich Prompting: System + Medical Rules + User Input
    full_prompt = ""
    if system_prompt:
        full_prompt += f"System: {system_prompt}\n"
    
    full_prompt += f"Domain Rules: {MEDICAL_GRAPH_PROMPT}\n"
    
    for msg in history_messages:
        full_prompt += f"{msg.get('role')}: {msg.get('content')}\n"
        
    full_prompt += f"User: {prompt}\nAnswer:"

    response = await model.generate_content_async(full_prompt)
    return response.text

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def gemini_embedding_func(texts: list[str]) -> np.ndarray:
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=texts,
            task_type="retrieval_document"
        )
        return np.array(result['embedding'])
    except Exception as e:
        print(f"Embedding Error: {e}")
        return np.zeros((len(texts), 768))