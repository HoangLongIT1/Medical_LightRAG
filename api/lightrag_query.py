"""
LightRAG Query API Routes
Handles queries with multiple search modes: naive, local, global, hybrid, mix.
"""

import logging
from typing import Optional, List, Dict, Any, Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from utils.lightrag_engine import LightRAGEngine

# Configure logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/lightrag", tags=["lightrag-query"])


# ============================
# Pydantic Models
# ============================

class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="The query text to search the knowledge graph",
    )
    mode: Literal["naive", "local", "global", "hybrid", "mix"] = Field(
        default="hybrid",
        description=(
            "Search mode:\n"
            "- **naive**: Simple vector similarity search (traditional RAG)\n"
            "- **local**: Entity-centric search using KG neighbors\n"
            "- **global**: Relationship-centric search using graph communities\n"
            "- **hybrid**: Combines local + global\n"
            "- **mix**: Combines naive + local + global (most comprehensive)"
        ),
    )
    only_need_context: bool = Field(
        default=False,
        description="If True, returns only the retrieved context without LLM generation",
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        description="Number of top items to retrieve",
    )
    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Conversation history for context. Format: [{'role': 'user/assistant', 'content': 'msg'}]",
    )


class QueryResponse(BaseModel):
    status: str = Field(description="Query execution status")
    query: str = Field(description="The original query")
    mode: str = Field(description="Search mode used")
    response: str = Field(description="The generated response or retrieved context")


# ============================
# Routes
# ============================

@router.post("/query", response_model=QueryResponse)
async def query_lightrag(request: QueryRequest):
    """
    Query the LightRAG knowledge graph with the specified search mode.

    ## Search Modes

    | Mode | Description | Best For |
    |------|-------------|----------|
    | `naive` | Simple vector similarity | Quick factual lookups |
    | `local` | Entity-centric via KG neighbors | Specific entity questions |
    | `global` | Graph community structure | Broad/thematic questions |
    | `hybrid` | local + global combined | General medical queries |
    | `mix` | naive + local + global | Most comprehensive results |

    ## Example Request

    ```json
    {
        "query": "Triệu chứng đau răng khôn là gì?",
        "mode": "hybrid",
        "only_need_context": false
    }
    ```
    """
    try:
        logger.info(f"🔍 LightRAG query - Mode: {request.mode}, Query: '{request.query[:80]}...'")

        # Build kwargs
        kwargs = {}
        if request.top_k is not None:
            kwargs["top_k"] = request.top_k

        response = await LightRAGEngine.query(
            query=request.query,
            mode=request.mode,
            only_need_context=request.only_need_context,
            conversation_history=request.conversation_history,
            **kwargs,
        )

        # Handle QueryResult object or string
        response_text = str(response) if not isinstance(response, str) else response

        return QueryResponse(
            status="success",
            query=request.query,
            mode=request.mode,
            response=response_text,
        )
    except Exception as e:
        logger.error(f"❌ Error in LightRAG query: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/query/context")
async def query_context_only(request: QueryRequest):
    """
    Retrieve only the context from LightRAG without LLM generation.

    Useful for debugging, inspecting what the retrieval finds,
    or for feeding context into a custom LLM pipeline (e.g., PocketFlow).
    """
    try:
        logger.info(f"🔍 LightRAG context query - Mode: {request.mode}, Query: '{request.query[:80]}...'")

        kwargs = {}
        if request.top_k is not None:
            kwargs["top_k"] = request.top_k

        context = await LightRAGEngine.query(
            query=request.query,
            mode=request.mode,
            only_need_context=True,
            **kwargs,
        )

        context_text = str(context) if not isinstance(context, str) else context

        return {
            "status": "success",
            "query": request.query,
            "mode": request.mode,
            "context": context_text,
        }
    except Exception as e:
        logger.error(f"❌ Error in context query: {e}")
        raise HTTPException(status_code=500, detail=f"Context query failed: {str(e)}")
