# Core framework import
from pocketflow import Node

# Standard library imports
import logging
import asyncio

# Configure logging for this module with Vietnam timezone
from utils.timezone_utils import setup_vietnam_logging
from config.logging_config import logging_config

if logging_config.USE_VIETNAM_TIMEZONE:
    logger = setup_vietnam_logging(__name__,
                                 level=getattr(logging, logging_config.LOG_LEVEL.upper()),
                                 format_str=logging_config.LOG_FORMAT)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, logging_config.LOG_LEVEL.upper()))


class RetrieveFromKBWithDemuc(Node):
    """
    Retrieve relevant context from LightRAG knowledge graph.

    Uses LightRAG's hybrid search (graph + vector) to find relevant
    entities, relationships, and text chunks for the given query.

    - prep(): Read query from shared store
    - exec(): Query LightRAG with hybrid mode, retrieving only context
    - post(): Write retrieved context to shared store for ComposeAnswer
    """

    def prep(self, shared):
        # Read from shared store ONLY
        query = shared.get("retrieval_query") or shared.get("query")
        return {
            "query": query,
        }

    def exec(self, inputs):
        from utils.lightrag_engine import LightRAGEngine

        retrieve_query = inputs["query"]

        logger.info(f"📚 [RetrieveFromKBWithDemuc] Querying LightRAG with: '{retrieve_query[:80]}...'")

        # Use Hybrid Search: BM25 keyword + LightRAG graph+vector
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're inside an async context (PocketFlow async flow)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    context = pool.submit(
                        asyncio.run,
                        LightRAGEngine.hybrid_query(
                            query=retrieve_query,
                        )
                    ).result()
            else:
                context = loop.run_until_complete(
                    LightRAGEngine.hybrid_query(
                        query=retrieve_query,
                    )
                )
        except RuntimeError:
            # No event loop exists
            context = asyncio.run(
                LightRAGEngine.hybrid_query(
                    query=retrieve_query,
                )
            )

        # Convert context to string if needed
        context_text = str(context) if not isinstance(context, str) else context

        logger.info(f"📚 [RetrieveFromKBWithDemuc] Retrieved context ({len(context_text)} chars)")
        logger.info(f"📚 [RetrieveFromKBWithDemuc] Context preview: {context_text[:200]}...")

        return {
            "context": context_text,
            "query": retrieve_query,
        }

    def post(self, shared, prep_res, exec_res):
        # Handle None exec_res (unhandled exceptions)
        if exec_res is None:
            logger.error("📚 [RetrieveFromKBWithDemuc] POST - exec_res is None, using empty context")
            shared["retrieved_context"] = ""
            shared["selected_questions"] = []
            shared["rag_state"] = "error"
            return "loop"

        # Save LightRAG context to shared store
        shared["retrieved_context"] = exec_res["context"]
        # Keep selected_questions as a summary for RagAgent to evaluate
        shared["selected_questions"] = exec_res["context"][:500] if exec_res["context"] else ""

        # Update RAG state
        shared["rag_state"] = "retrieved"

        logger.info(f"📚 [RetrieveFromKBWithDemuc] POST - Context stored ({len(exec_res['context'])} chars)")

        # Route based on where we came from
        if shared.get("from_better_query", False):
            shared["from_better_query"] = False
            return "compose"  # Go to compose_answer
        else:
            return "loop"  # Go back to rag_agent


