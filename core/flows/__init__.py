"""
Flow definitions for medical chatbot.

- MedFlow: Original RAG pipeline (legacy, still functional)
- AdvancedMedicalFlow: 5-layer multi-agent pipeline with LightRAG
"""

from .medical_flow import MedFlow
from .advanced_medical_flow import AdvancedMedicalFlow

__all__ = [
    "MedFlow",
    "AdvancedMedicalFlow",
]
