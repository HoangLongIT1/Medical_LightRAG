"""
FastAPI server for Medical Conversation System
Main application entry point with LightRAG integration
"""

import logging
import uvicorn
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

from utils.timezone_utils import get_vietnam_time, setup_vietnam_logging
from config.logging_config import logging_config

# Configure logging
if logging_config.USE_VIETNAM_TIMEZONE:
    logger = setup_vietnam_logging(
        __name__,
        level=getattr(logging, logging_config.LOG_LEVEL.upper()),
        format_str=logging_config.LOG_FORMAT
    )
else:
    logging.basicConfig(
        level=getattr(logging, logging_config.LOG_LEVEL.upper()),
        format=logging_config.LOG_FORMAT
    )
    logger = logging.getLogger(__name__)


# Lifespan context manager (replaces deprecated on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events"""
    # ===== STARTUP =====
    logger.info("🚀 Starting Medical Conversation API...")

    # Initialize LightRAG engine
    logger.info("🔄 Initializing LightRAG engine...")
    try:
        from utils.lightrag_engine import LightRAGEngine
        await LightRAGEngine.initialize()
        logger.info("✅ LightRAG engine initialized successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to initialize LightRAG engine: {str(e)}")
        logger.error("⚠️  API will continue but LightRAG features may be limited")

    logger.info("🎉 All startup tasks completed!")

    yield  # Application is running

    # ===== SHUTDOWN =====
    logger.info("🛑 Shutting down Medical Conversation API...")
    try:
        from utils.lightrag_engine import LightRAGEngine
        await LightRAGEngine.shutdown()
        logger.info("✅ LightRAG engine shut down gracefully")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {str(e)}")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Medical Conversation API",
    description="AI-powered medical consultation system using LightRAG + PocketFlow",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/redoc",
    swagger_ui_oauth2_redirect_url="/api/docs/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": "",
        "clientSecret": "",
    }
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Exception",
            "message": exc.detail,
            "timestamp": get_vietnam_time().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"❌ Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": get_vietnam_time().isoformat(),
        },
    )


# Root endpoint
@app.get("/api")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Medical Conversation API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/health",
    }


# Include routers
from api import auth_router, users_router, health_router, chat_router, threads_router, lightrag_docs_router, lightrag_query_router

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(threads_router)
app.include_router(lightrag_docs_router)
app.include_router(lightrag_query_router)

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    logger.info(f"🚀 Starting Medical Conversation API on {host}:{port}")
    logger.info(f"📖 API Documentation: http://{host}:{port}/api/docs")

    uvicorn.run("app:app", host=host, port=port, reload=debug, log_level="info")
