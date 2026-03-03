"""Knowledge base utility package.

Uses LightRAG for document retrieval (graph+vector RAG).
Memory retrieval utilities are imported directly by memory nodes.
Metadata utilities provide topic/category classification helpers.
"""

# Only export metadata utils at package level
# memory_retrieval is imported directly by memory nodes to avoid
# loading Qdrant dependencies at import time
from .metadata_utils import *
