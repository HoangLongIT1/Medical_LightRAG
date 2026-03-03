"""Node definitions for medical chatbot flows.

Each node lives in its own module. This file re-exports those
classes for convenient imports like `from core.nodes import IngestQuery`.
"""

# Core pipeline nodes
from .IngestQuery import IngestQuery
from .ComposeAnswer import ComposeAnswer
from .FallbackNode import FallbackNode

# Legacy RAG pipeline nodes (used by MedFlow)
from .DecideSummarizeConversationToRetriveOrDirectlyAnswer import DecideSummarizeConversationToRetriveOrDirectlyAnswer
from .RetrieveFromKBWithDemuc import RetrieveFromKBWithDemuc
from .RagAgent import RagAgent
from .QueryExpandAgent import QueryExpandAgent
from .TopicClassifyAgent import TopicClassifyAgent
from .QueryCreatingForRetrievalAgent import QueryCreatingForRetrievalAgent

# Advanced medical nodes (AdvancedMedicalFlow - Layer 1-3)
from .ClinicalStateManager import ClinicalStateManager
from .MasterMedicalRouter import MasterMedicalRouter
from .SpecialistAgents import (
    InternalMedicineAgent, PediatricsAgent, PharmacologyAgent,
    SurgeryAgent, OdontologyAgent,
    ObstetricsAgent, DermatologyAgent, PsychiatryAgent,
)

# Memory management nodes
from .MemoryManager import MemoryManager
from .AddMemory import AddMemory
from .UpdateMemory import UpdateMemory
from .DeleteMemory import DeleteMemory
from .RetrieveFromMemory import RetrieveFromMemory

__all__ = [
    # Core
    "IngestQuery",
    "ComposeAnswer",
    "FallbackNode",
    # Legacy RAG
    "DecideSummarizeConversationToRetriveOrDirectlyAnswer",
    "RetrieveFromKBWithDemuc",
    "RagAgent",
    "QueryExpandAgent",
    "TopicClassifyAgent",
    "QueryCreatingForRetrievalAgent",
    # Advanced medical (Layer 1-3)
    "ClinicalStateManager",
    "MasterMedicalRouter",
    "InternalMedicineAgent",
    "PediatricsAgent",
    "PharmacologyAgent",
    "SurgeryAgent",
    "OdontologyAgent",
    "ObstetricsAgent",
    "DermatologyAgent",
    "PsychiatryAgent",
    # Memory
    "MemoryManager",
    "AddMemory",
    "UpdateMemory",
    "DeleteMemory",
    "RetrieveFromMemory",
]
