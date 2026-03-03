"""
LightRAG Engine - Singleton wrapper for LightRAG instance.

Provides:
- Async initialization with Gemini LLM
- Query with multiple search modes (naive, local, global, hybrid, mix)
- Document insertion with incremental updates
- Graceful lifecycle management
"""

import os
import logging
import asyncio
from typing import Optional

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

    # Build the full prompt
    full_prompt = ""
    if system_prompt:
        full_prompt += f"{system_prompt}\n\n"

    if history_messages:
        for msg in history_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            full_prompt += f"[{role}]: {content}\n"
        full_prompt += "\n"

    full_prompt += prompt

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
                model="gemini-embedding-exp-03-07",
                contents=batch,
            )
            for embedding in response.embeddings:
                embeddings.append(embedding.values)

        return embeddings
    except Exception as e:
        logger.error(f"❌ Gemini embedding call failed: {e}")
        raise


# ============================================================================
# LightRAG Engine Singleton
# ============================================================================

class LightRAGEngine:
    """
    Singleton wrapper for LightRAG instance.
    Manages initialization, lifecycle, and provides convenience methods.
    """

    _instance = None  # LightRAG instance
    _initialized = False

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
                llm_model_max_async=lightrag_config.LLM_MAX_ASYNC,
                llm_model_max_token_size=lightrag_config.LLM_MAX_TOKENS,
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
