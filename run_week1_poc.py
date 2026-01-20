import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import traceback
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from src.config import WORK_DIR, EMBEDDING_DIM, MAX_TOKEN_SIZE
from src.core.gemini_client import gemini_llm_func, gemini_embedding_func

SAMPLE_TEXT = """
CASE STUDY: DIABETIC KETOACIDOSIS (DKA)
A 25-year-old patient with Type 1 Diabetes presents with severe nausea, vomiting, and abdominal pain.
Physical exam reveals Kussmaul respirations and a fruity breath odor.
Lab results show Hyperglycemia and metabolic acidosis.
Treatment involves aggressive IV fluids (Normal Saline) and Insulin infusion.
Potassium levels must be monitored as Insulin causes hypokalemia.
"""

async def main():
    try:
        print(f"Starting LightRAG Medical Agent in: {WORK_DIR}")
        
        # 1. Initialize Core
        rag = LightRAG(
            working_dir=WORK_DIR,
            llm_model_func=gemini_llm_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=EMBEDDING_DIM, 
                max_token_size=MAX_TOKEN_SIZE, 
                func=gemini_embedding_func
            ),
            chunk_token_size=512
        )

        # 2. Init Storage (Crucial Step)
        await rag.initialize_storages()

        # 3. Ingest Data
        print("\nIngesting sample medical data...")
        await rag.ainsert(SAMPLE_TEXT)
        print("Ingestion Complete.")

        # 4. Test Query
        print("\nTesting Query...")
        question = "What are the treatments and risks for DKA described in the text?"
        result = await rag.aquery(question, param=QueryParam(mode="hybrid"))
        
        print("\n" + "="*40)
        print("MEDICAL AGENT ANSWER:")
        print(result)
        print("="*40)

    except Exception as e:
        print("\nCRITICAL ERROR:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
    input("\n[DONE] Press Enter to exit...")