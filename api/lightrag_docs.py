"""
LightRAG Document Management API Routes
Handles document insertion, incremental updates, and deletion.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from utils.lightrag_engine import LightRAGEngine

# Configure logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/lightrag/documents", tags=["lightrag-documents"])


# ============================
# Pydantic Models
# ============================

class InsertTextRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Text content to insert into LightRAG")
    description: str = Field(default="", description="Optional description for the document")


class InsertTextResponse(BaseModel):
    status: str
    message: str
    content_length: int


class BatchInsertRequest(BaseModel):
    contents: List[str] = Field(..., min_length=1, description="List of text contents to insert")


class BatchInsertResponse(BaseModel):
    status: str
    message: str
    total_inserted: int
    total_chars: int


class DeleteEntityRequest(BaseModel):
    entity_name: str = Field(..., min_length=1, description="Name of the entity to delete")


class StatusResponse(BaseModel):
    status: str
    working_dir: str = ""
    llm_model: str = ""
    graph_storage: str = ""
    vector_storage: str = ""
    error: str = ""


# ============================
# Routes
# ============================

@router.post("/text", response_model=InsertTextResponse)
async def insert_text(request: InsertTextRequest):
    """
    Insert text content into LightRAG.

    LightRAG will automatically:
    - Chunk the text into appropriate segments
    - Extract entities and relationships
    - Build/update the knowledge graph incrementally
    - Create vector embeddings for search

    This is an **incremental update** - new content is added without
    reprocessing existing data.
    """
    try:
        logger.info(f"📄 Inserting text ({len(request.content)} chars)")
        await LightRAGEngine.insert_text(request.content)

        return InsertTextResponse(
            status="success",
            message=f"Successfully inserted text ({len(request.content)} chars) into LightRAG",
            content_length=len(request.content),
        )
    except Exception as e:
        logger.error(f"❌ Error inserting text: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to insert text: {str(e)}")


@router.post("/batch", response_model=BatchInsertResponse)
async def batch_insert(request: BatchInsertRequest):
    """
    Insert multiple text contents in batch.

    Each item is inserted incrementally - existing knowledge graph
    entities and relationships are preserved and extended.
    """
    try:
        total_chars = sum(len(c) for c in request.contents)
        logger.info(f"📄 Batch inserting {len(request.contents)} documents ({total_chars} total chars)")

        await LightRAGEngine.insert_batch(request.contents)

        return BatchInsertResponse(
            status="success",
            message=f"Successfully inserted {len(request.contents)} documents",
            total_inserted=len(request.contents),
            total_chars=total_chars,
        )
    except Exception as e:
        logger.error(f"❌ Error in batch insert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to batch insert: {str(e)}")


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get the current status of the LightRAG engine.

    Returns information about the working directory, LLM model,
    and storage backends.
    """
    try:
        status = await LightRAGEngine.get_processing_status()
        return StatusResponse(**status)
    except Exception as e:
        logger.error(f"❌ Error getting status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.delete("/entity")
async def delete_entity(request: DeleteEntityRequest):
    """
    Delete an entity and its related relationships from the knowledge graph.

    This removes the entity node and all edges connected to it.
    """
    try:
        logger.info(f"🗑️ Deleting entity: {request.entity_name}")
        await LightRAGEngine.delete_by_entity(request.entity_name)

        return {
            "status": "success",
            "message": f"Deleted entity '{request.entity_name}' and its relationships",
        }
    except Exception as e:
        logger.error(f"❌ Error deleting entity: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete entity: {str(e)}")
