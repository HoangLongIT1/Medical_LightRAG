"""
LightRAG Configuration
Reads settings from environment variables for the LightRAG engine.
"""

import os
from dataclasses import dataclass, field


@dataclass
class LightRAGConfig:
    """Configuration for LightRAG engine"""

    # Working directory for LightRAG storage files
    WORKING_DIR: str = field(
        default_factory=lambda: os.getenv("LIGHTRAG_WORKING_DIR", "./lightrag_data")
    )

    # LLM Configuration
    LLM_MODEL: str = field(
        default_factory=lambda: os.getenv("LIGHTRAG_LLM_MODEL", "gemini-2.5-flash-lite")
    )
    LLM_MAX_TOKENS: int = field(
        default_factory=lambda: int(os.getenv("LIGHTRAG_MAX_TOKENS", "32768"))
    )
    LLM_MAX_ASYNC: int = field(
        default_factory=lambda: int(os.getenv("LIGHTRAG_MAX_ASYNC", "4"))
    )

    # Chunking Configuration
    CHUNK_SIZE: int = field(
        default_factory=lambda: int(os.getenv("LIGHTRAG_CHUNK_SIZE", "1200"))
    )
    CHUNK_OVERLAP: int = field(
        default_factory=lambda: int(os.getenv("LIGHTRAG_CHUNK_OVERLAP", "100"))
    )

    # Storage backends
    GRAPH_STORAGE: str = field(
        default_factory=lambda: os.getenv("LIGHTRAG_GRAPH_STORAGE", "NetworkXStorage")
    )
    VECTOR_STORAGE: str = field(
        default_factory=lambda: os.getenv("LIGHTRAG_VECTOR_STORAGE", "NanoVectorDBStorage")
    )
    KV_STORAGE: str = field(
        default_factory=lambda: os.getenv("LIGHTRAG_KV_STORAGE", "JsonKVStorage")
    )

    # Gemini API Key (shared with main app)
    GEMINI_API_KEY: str = field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY", "")
    )


# Singleton config instance
lightrag_config = LightRAGConfig()
