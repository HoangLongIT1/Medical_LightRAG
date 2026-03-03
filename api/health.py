"""
Health check and system information API endpoints
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from utils.timezone_utils import get_vietnam_time
from utils.role_enum import RoleEnum, ROLE_DISPLAY_NAME, ROLE_DESCRIPTION

# Configure logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["health"])


# Pydantic models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    message: str | None = None


class RoleInfo(BaseModel):
    id: str = Field(..., description="Role identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Role description")


class RolesResponse(BaseModel):
    roles: List[RoleInfo] = Field(..., description="Available roles")
    default_role: str = Field(..., description="Default role identifier")
    timestamp: str = Field(..., description="Response timestamp")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint with LightRAG engine status.
    """
    try:
        from utils.lightrag_engine import LightRAGEngine
        engine = LightRAGEngine()
        lightrag_ready = engine._rag is not None
    except Exception:
        lightrag_ready = False

    status = "healthy" if lightrag_ready else "degraded"

    return HealthResponse(
        status=status,
        timestamp=get_vietnam_time().isoformat(),
        version="2.0.0",
        message=f"LightRAG Engine: {'Ready' if lightrag_ready else 'Not Initialized'}"
    )


@router.get("/roles", response_model=RolesResponse)
async def get_available_roles():
    """
    Get available user roles for medical conversations.
    """
    try:
        # Filter out orthodontist role from frontend response
        filtered_roles = [r for r in RoleEnum if r != RoleEnum.ORTHODONTIST]
        
        roles = [
            RoleInfo(
                id=r.value,
                name=ROLE_DISPLAY_NAME[r],
                description=ROLE_DESCRIPTION[r],
            )
            for r in filtered_roles
        ]

        return RolesResponse(
            roles=roles,
            default_role=RoleEnum.PATIENT_DENTAL.value,
            timestamp=get_vietnam_time().isoformat(),
        )

    except Exception as e:
        logger.error(f"❌ Error getting roles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving roles: {str(e)}")
