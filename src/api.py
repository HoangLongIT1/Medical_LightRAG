import asyncio
from lightrag import LightRAG
from lightrag.utils import EmbeddingFunc
from src.core.gemini_client import gemini_llm_func, gemini_embedding_func
from src.config import WORK_DIR

# Biến global để giữ instance của RAG (tránh load lại nhiều lần)
_RAG_INSTANCE = None

async def get_rag_instance():
    global _RAG_INSTANCE
    if _RAG_INSTANCE is None:
        print("Loading RAG System...")
        _RAG_INSTANCE = LightRAG(
            working_dir=WORK_DIR,
            llm_model_func=gemini_llm_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=768, 
                max_token_size=8192, 
                func=gemini_embedding_func
            )
        )
        await _RAG_INSTANCE.initialize_storages()
        print("RAG System Ready!")
    return _RAG_INSTANCE

async def ingest_new_document(text_content: str):
    """
    Member 2 gọi hàm này để nạp text sạch vào hệ thống
    """
    rag = await get_rag_instance()
    await rag.ainsert(text_content)
    return "Ingestion success"

async def query_knowledge_base(question: str):
    """
    Member 4 gọi hàm này để test câu hỏi
    """
    rag = await get_rag_instance()
    # Dùng mode hybrid cho kết quả tốt nhất kết hợp local graph + global summary
    response = await rag.aquery(question, param=QueryParam(mode="hybrid"))
    return response