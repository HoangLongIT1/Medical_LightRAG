import os
from dotenv import load_dotenv

load_dotenv()

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK_DIR = os.path.join(BASE_DIR, "data", "knowledge_graph")

if not os.path.exists(WORK_DIR):
    os.makedirs(WORK_DIR)

# --- GOOGLE GEMINI SETUP ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
EMBEDDING_MODEL = "models/text-embedding-004"
EMBEDDING_DIM = 768
MAX_TOKEN_SIZE = 8192

# --- MEDICAL DOMAIN PROMPT ---
MEDICAL_GRAPH_PROMPT = """
You are a Medical AI Assistant. Extract entities and relations from the text.
Target Entities: Disease, Symptom, Drug, Treatment, Anatomy, Test, SideEffect.
Target Relations: TREATS, CAUSES, HAS_SIDE_EFFECT, PREVENTS, DIAGNOSED_BY, LOCATED_IN.
Rules:
1. Output strictly in JSON format.
2. Translate synonyms to standard medical terms.
3. Only extract explicitly stated relations.
"""