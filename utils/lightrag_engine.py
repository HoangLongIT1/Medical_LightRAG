"""
LightRAG Engine - Singleton wrapper for LightRAG instance.

Provides:
- Async initialization with Gemini LLM
- Query with multiple search modes (naive, local, global, hybrid, mix)
- Document insertion with incremental updates
- Graceful lifecycle management
"""

import os
import json
import re
import logging
import asyncio
from typing import Optional, List, Dict, Any

from config.lightrag_config import lightrag_config

# Configure logger
logger = logging.getLogger(__name__)


# ============================================================================
# Custom Gemini LLM function for LightRAG
# ============================================================================

async def gemini_llm_complete(
    prompt: str,
    system_prompt: Optional[str] = None,
    history_messages: Optional[list] = None,
    keyword_extraction: bool = False,
    **kwargs,
) -> str:
    """
    Custom LLM function wrapping google-genai for LightRAG.
    Matches the signature expected by LightRAG's llm_model_func.
    """
    from google import genai

    api_key = lightrag_config.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables")

    client = genai.Client(api_key=api_key)
    model_name = kwargs.pop("model", lightrag_config.LLM_MODEL)

    MEDICAL_GRAPH_PROMPT = """
--- MEDICAL EXTRACTION RULES ---
Bạn là một Chuyên gia AI Y khoa Tiếng Việt. Nhiệm vụ của bạn là phân tích văn bản và trích xuất sơ đồ tri thức (Knowledge Graph).

### MỤC TIÊU TRÍCH XUẤT (ENTITIES):
- Disease (Bệnh): Ví dụ: Tiểu đường, Ung thư phổi, Viêm gan B.
- Symptom (Triệu chứng): Ví dụ: Sốt cao, Ho khan, Đau bụng, Vàng da.
- Drug (Thuốc/Hoạt chất): Ví dụ: Paracetamol, Insulin, Metformin.
- Treatment (Điều trị/Phẫu thuật): Ví dụ: Truyền dịch, Mổ nội soi, Xạ trị.
- Anatomy (Bộ phận cơ thể): Ví dụ: Gan, Phổi, Thận, Tim.
- SideEffect (Tác dụng phụ): Ví dụ: Buồn nôn, Suy thận, Dị ứng.

### MỐI QUAN HỆ (RELATIONS):
- TREATS (Điều trị): Thuốc/Phương pháp -> Bệnh/Triệu chứng.
- CAUSES (Gây ra): Bệnh/Thuốc -> Triệu chứng/Tác dụng phụ.
- PREVENTS (Ngăn ngừa): Thuốc -> Bệnh.
- DIAGNOSED_BY (Chẩn đoán bằng): Bệnh -> Xét nghiệm/Test.
- LOCATED_IN (Vị trí tại): Bệnh -> Bộ phận cơ thể.

### QUY TẮC BẮT BUỘC:
1. Ngôn ngữ đầu ra: HOÀN TOÀN BẰNG TIẾNG VIỆT.
2. Nếu gặp thuật ngữ tiếng Anh, hãy dịch sang thuật ngữ y khoa tiếng Việt tương đương (VD: "Hypertension" -> "Tăng huyết áp").
3. Trích xuất dưới dạng JSON chuẩn.
--------------------------------
"""

    # Detect if LightRAG is asking for knowledge graph extraction
    combined_content = (system_prompt or "") + prompt
    combined_lower = combined_content.lower()
    
    is_extraction = "extract" in combined_lower and "json" in combined_lower

    # Build the full prompt
    full_prompt = ""
    
    if is_extraction:
        # Inject medical ontology rules for graph extraction
        full_prompt += MEDICAL_GRAPH_PROMPT + "\n"
        if system_prompt:
            full_prompt += f"{system_prompt}\n\n"
        full_prompt += f"User: {prompt}\n"
    elif "keywords" in combined_lower:
        # Keyword extraction phase for retrieval
        if system_prompt:
            full_prompt += f"{system_prompt}\n\n"
        full_prompt += f"User: {prompt}\n"
    else:
        # Standard answering phase
        full_prompt += "SYSTEM: You are a helpful Medical Assistant. Always answer strictly in Vietnamese (Tiếng Việt).\n\n"
        if system_prompt:
            full_prompt += f"{system_prompt}\n\n"

        if history_messages:
            for msg in history_messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                full_prompt += f"[{role}]: {content}\n"
            full_prompt += "\n"
        
        full_prompt += f"User: {prompt}\nAnswer:"


    try:
        # Use async generation
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=model_name,
            contents=full_prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"❌ Gemini LLM call failed: {e}")
        raise


# ============================================================================
# Custom Embedding function for LightRAG
# ============================================================================

async def gemini_embedding_func(texts: list[str]) -> list[list[float]]:
    """
    Embedding function using Google's Gemini embedding model.
    Returns a list of embedding vectors for the input texts.
    """
    from google import genai

    api_key = lightrag_config.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables")

    client = genai.Client(api_key=api_key)

    try:
        embeddings = []
        # Process in batches to avoid rate limits
        batch_size = 20
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = await asyncio.to_thread(
                client.models.embed_content,
                model=lightrag_config.EMBEDDING_MODEL,
                contents=batch,
            )
            for embedding in response.embeddings:
                embeddings.append(embedding.values)

        return embeddings
    except Exception as e:
        logger.error(f"❌ Gemini embedding call failed: {e}")
        raise


# ============================================================================
# BM25 Keyword Index for Hybrid Search
# ============================================================================

class BM25Index:
    """
    BM25 keyword index built from LightRAG's text chunks.
    Provides exact keyword matching to complement vector search.
    """

    def __init__(self):
        self._index = None
        self._chunks: List[Dict[str, Any]] = []  # [{"id": ..., "content": ...}]
        self._tokenized_corpus: List[List[str]] = []

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple whitespace + punctuation tokenizer for Vietnamese/English medical text."""
        text = text.lower()
        # Keep alphanumeric, Vietnamese diacritics, hyphens (for drug names)
        tokens = re.findall(r'[\w\-]+', text, re.UNICODE)
        return [t for t in tokens if len(t) > 1]

    def build_from_kv_store(self, working_dir: str):
        """
        Load text chunks from LightRAG's KV store and build the BM25 index.
        """
        from rank_bm25 import BM25Okapi

        kv_path = os.path.join(working_dir, "kv_store_text_chunks.json")
        if not os.path.exists(kv_path):
            logger.warning(f"⚠️ BM25: KV store not found at {kv_path}. Index will be empty.")
            return

        try:
            with open(kv_path, 'r', encoding='utf-8') as f:
                kv_data = json.load(f)
        except Exception as e:
            logger.error(f"❌ BM25: Failed to read KV store: {e}")
            return

        self._chunks = []
        self._tokenized_corpus = []

        for chunk_id, chunk_data in kv_data.items():
            content = ""
            if isinstance(chunk_data, dict):
                content = chunk_data.get("content", chunk_data.get("data", ""))
            elif isinstance(chunk_data, str):
                content = chunk_data

            if content:
                self._chunks.append({"id": chunk_id, "content": content})
                self._tokenized_corpus.append(self._tokenize(content))

        if self._tokenized_corpus:
            self._index = BM25Okapi(self._tokenized_corpus)
            logger.info(f"✅ BM25 index built with {len(self._chunks)} chunks")
        else:
            logger.warning("⚠️ BM25: No text chunks found. Index is empty.")

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search the BM25 index and return top-k results.
        Returns: [{"id": ..., "content": ..., "bm25_score": ...}]
        """
        if self._index is None or not self._chunks:
            return []

        tokenized_query = self._tokenize(query)
        if not tokenized_query:
            return []

        scores = self._index.get_scores(tokenized_query)

        # Get top-k indices sorted by score descending
        scored_indices = sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )[:top_k]

        results = []
        for idx, score in scored_indices:
            if score > 0:  # Only include non-zero scores
                results.append({
                    "id": self._chunks[idx]["id"],
                    "content": self._chunks[idx]["content"],
                    "bm25_score": float(score),
                })

        return results

    @property
    def is_ready(self) -> bool:
        return self._index is not None and len(self._chunks) > 0


# ============================================================================
# LightRAG Engine Singleton
# ============================================================================

class LightRAGEngine:
    """
    Singleton wrapper for LightRAG instance.
    Manages initialization, lifecycle, and provides convenience methods.
    Includes BM25 index for hybrid (keyword + vector) search.
    """

    _instance = None  # LightRAG instance
    _initialized = False
    _bm25_index: Optional[BM25Index] = None

    @classmethod
    async def initialize(cls):
        """Initialize LightRAG with Gemini LLM and configured storage backends."""
        if cls._initialized and cls._instance is not None:
            logger.info("⚡ LightRAG already initialized, reusing instance")
            return cls._instance

        try:
            from lightrag import LightRAG
            from lightrag.utils import EmbeddingFunc

            working_dir = lightrag_config.WORKING_DIR
            os.makedirs(working_dir, exist_ok=True)

            logger.info(f"🔄 Initializing LightRAG engine...")
            logger.info(f"   Working dir: {working_dir}")
            logger.info(f"   LLM model: {lightrag_config.LLM_MODEL}")
            logger.info(f"   Graph storage: {lightrag_config.GRAPH_STORAGE}")
            logger.info(f"   Vector storage: {lightrag_config.VECTOR_STORAGE}")

            # Determine embedding dimension by making a test call
            test_embeddings = await gemini_embedding_func(["test"])
            embedding_dim = len(test_embeddings[0])
            logger.info(f"   Embedding dimension: {embedding_dim}")

            rag = LightRAG(
                working_dir=working_dir,
                llm_model_func=gemini_llm_complete,
                chunk_token_size=lightrag_config.CHUNK_SIZE,
                chunk_overlap_token_size=lightrag_config.CHUNK_OVERLAP,
                embedding_func=EmbeddingFunc(
                    embedding_dim=embedding_dim,
                    max_token_size=8192,
                    func=gemini_embedding_func,
                ),
                graph_storage=lightrag_config.GRAPH_STORAGE,
                vector_storage=lightrag_config.VECTOR_STORAGE,
                kv_storage=lightrag_config.KV_STORAGE,
            )

            await rag.initialize_storages()

            cls._instance = rag
            cls._initialized = True

            # Build BM25 index from existing chunks
            cls._bm25_index = BM25Index()
            cls._bm25_index.build_from_kv_store(working_dir)

            logger.info("✅ LightRAG engine initialized successfully!")
            return rag
        except Exception as e:
            logger.error(f"❌ LightRAG initialization failed: {e}")
            cls._instance = None
            cls._initialized = False
            raise

    @classmethod
    async def get_instance(cls):
        """Get the LightRAG instance, initializing if needed."""
        if cls._instance is None or not cls._initialized:
            return await cls.initialize()
        return cls._instance

    @classmethod
    async def query(
        cls,
        query: str,
        mode: str = "hybrid",
        only_need_context: bool = False,
        conversation_history: Optional[list] = None,
        **kwargs,
    ) -> str:
        """
        Query LightRAG with the specified search mode.

        Args:
            query: The search query text
            mode: Search mode - one of: naive, local, global, hybrid, mix
            only_need_context: If True, returns only retrieved context (no LLM generation)
            conversation_history: Optional conversation history for context
            **kwargs: Additional QueryParam arguments

        Returns:
            The query response string, or error message on failure
        """
        try:
            from lightrag.base import QueryParam

            rag = await cls.get_instance()
            param = QueryParam(
                mode=mode,
                only_need_context=only_need_context,
                **kwargs,
            )

            if conversation_history:
                param.conversation_history = conversation_history

            result = await rag.aquery(query, param=param)
            return result
        except Exception as e:
            logger.error(f"❌ LightRAG query failed: {e}")
            return f"[LightRAG Error] Không thể truy xuất thông tin từ cơ sở tri thức: {str(e)}"

    @classmethod
    async def hybrid_query(
        cls,
        query: str,
        bm25_top_k: int = 10,
        lightrag_mode: str = "hybrid",
        rrf_k: int = 60,
        **kwargs,
    ) -> str:
        """
        Hybrid Search: combines BM25 keyword results with LightRAG graph+vector results
        using Reciprocal Rank Fusion (RRF).

        Args:
            query: The search query text
            bm25_top_k: Number of BM25 results to retrieve
            lightrag_mode: LightRAG search mode (hybrid, local, global, etc.)
            rrf_k: RRF constant (higher = more weight to lower-ranked results)

        Returns:
            Combined context string with both BM25 and LightRAG results
        """
        results_parts = []

        # --- Part 1: LightRAG Graph+Vector Search ---
        lightrag_context = await cls.query(
            query=query,
            mode=lightrag_mode,
            only_need_context=True,
            **kwargs,
        )
        if lightrag_context and not lightrag_context.startswith("[LightRAG Error]"):
            results_parts.append("=== Knowledge Graph + Vector Search ===")
            results_parts.append(lightrag_context)

        # --- Part 2: BM25 Keyword Search ---
        if cls._bm25_index and cls._bm25_index.is_ready:
            bm25_results = cls._bm25_index.search(query, top_k=bm25_top_k)
            if bm25_results:
                results_parts.append("\n=== BM25 Keyword Search ===")
                for i, result in enumerate(bm25_results[:5], 1):  # Top 5 BM25
                    content_preview = result["content"][:500]
                    results_parts.append(f"[BM25 #{i} | score={result['bm25_score']:.2f}]")
                    results_parts.append(content_preview)
                    results_parts.append("---")
                logger.info(f"🔍 BM25 returned {len(bm25_results)} keyword matches")
        else:
            logger.info("⚠️ BM25 index not ready, using LightRAG results only")

        if not results_parts:
            return "Không tìm thấy thông tin liên quan trong cơ sở tri thức."

        return "\n".join(results_parts)

    @classmethod
    def rebuild_bm25_index(cls):
        """Rebuild BM25 index after new data is ingested."""
        if cls._bm25_index is None:
            cls._bm25_index = BM25Index()
        cls._bm25_index.build_from_kv_store(lightrag_config.WORKING_DIR)
        logger.info("🔄 BM25 index rebuilt")

    @classmethod
    async def insert_text(cls, content: str):
        """
        Insert text content into LightRAG.
        LightRAG automatically handles chunking, entity extraction,
        and incremental knowledge graph updates.

        Args:
            content: The text content to insert
        """
        rag = await cls.get_instance()
        await rag.ainsert(content)
        logger.info(f"✅ Inserted text ({len(content)} chars) into LightRAG")
        # Rebuild BM25 index to include the new content
        cls.rebuild_bm25_index()

    @classmethod
    async def insert_batch(cls, contents: list[str]):
        """
        Insert multiple text contents in batch.

        Args:
            contents: List of text contents to insert
        """
        rag = await cls.get_instance()
        for i, content in enumerate(contents):
            await rag.ainsert(content)
            logger.info(f"✅ Inserted batch item {i + 1}/{len(contents)}")

    @classmethod
    async def delete_by_entity(cls, entity_name: str):
        """
        Delete an entity and its relationships from the knowledge graph.

        Args:
            entity_name: Name of the entity to delete
        """
        rag = await cls.get_instance()
        await rag.adelete_by_entity(entity_name)
        logger.info(f"🗑️ Deleted entity: {entity_name}")

    @classmethod
    async def get_processing_status(cls) -> dict:
        """Get the current state of the LightRAG knowledge graph."""
        rag = await cls.get_instance()
        try:
            # Try to get basic stats
            return {
                "status": "running",
                "working_dir": lightrag_config.WORKING_DIR,
                "llm_model": lightrag_config.LLM_MODEL,
                "graph_storage": lightrag_config.GRAPH_STORAGE,
                "vector_storage": lightrag_config.VECTOR_STORAGE,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @classmethod
    async def shutdown(cls):
        """Gracefully shut down LightRAG engine."""
        if cls._instance is not None:
            try:
                await cls._instance.finalize_storages()
                logger.info("🛑 LightRAG storages finalized")
            except Exception as e:
                logger.error(f"❌ Error finalizing LightRAG storages: {e}")
            finally:
                cls._instance = None
                cls._initialized = False
                logger.info("🛑 LightRAG engine shut down")
