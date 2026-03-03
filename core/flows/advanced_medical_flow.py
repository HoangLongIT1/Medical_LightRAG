# core/flows/advanced_medical_flow.py
"""
Advanced Medical Flow (Full Multi-Agent Pipeline)

Architecture:

Layer 1 (Cognitive): IngestQuery → ClinicalStateManager
Layer 2 (Routing):   MasterMedicalRouter
Layer 3 (Execution): 8 Specialist Agents → RetrieveFromKBWithDemuc (LightRAG)
Layer 4 (Output):    ComposeAnswer (with safety disclaimer)
Layer 5 (Memory):    MemoryManager → Add/Update/Delete Memory

Specialist routes:
  noi_khoa   → InternalMedicineAgent
  nhi_khoa   → PediatricsAgent
  duoc_ly    → PharmacologyAgent
  ngoai_khoa → SurgeryAgent
  nha_khoa   → OdontologyAgent
  san_khoa   → ObstetricsAgent
  da_lieu    → DermatologyAgent
  tam_than   → PsychiatryAgent
  chitchat   → ComposeAnswer (direct)
"""

import logging
from core.pocketflow import Flow

# --- LAYER 1: Cognitive Layer ---
from core.nodes.IngestQuery import IngestQuery
from core.nodes.ClinicalStateManager import ClinicalStateManager

# --- LAYER 2: Routing & Safety ---
from core.nodes.MasterMedicalRouter import MasterMedicalRouter

# --- LAYER 3: Specialist Agents (8 specialists) ---
from core.nodes.SpecialistAgents import (
    InternalMedicineAgent,
    PediatricsAgent,
    PharmacologyAgent,
    SurgeryAgent,
    OdontologyAgent,
    ObstetricsAgent,
    DermatologyAgent,
    PsychiatryAgent,
)

# --- LAYER 3 (continued): LightRAG Retrieval ---
from core.nodes.RetrieveFromKBWithDemuc import RetrieveFromKBWithDemuc

# --- LAYER 4: Output ---
from core.nodes.ComposeAnswer import ComposeAnswer
from core.nodes.FallbackNode import FallbackNode

# --- LAYER 5: Memory Management ---
from core.nodes.MemoryManager import MemoryManager
from core.nodes.AddMemory import AddMemory
from core.nodes.UpdateMemory import UpdateMemory
from core.nodes.DeleteMemory import DeleteMemory


class AdvancedMedicalFlow(Flow):
    def __init__(self):
        # =============================================
        # 1. INITIALIZE ALL NODES
        # =============================================
        
        # Layer 1: Cognitive
        ingest = IngestQuery()
        state_manager = ClinicalStateManager(max_retries=2, wait=1)
        
        # Layer 2: Routing
        master_router = MasterMedicalRouter(max_retries=2, wait=1)
        
        # Layer 3: Specialist Agents (8 specialists)
        internal_med = InternalMedicineAgent(max_retries=2, wait=1)
        pediatrics = PediatricsAgent(max_retries=2, wait=1)
        pharmacology = PharmacologyAgent(max_retries=2, wait=1)
        surgery = SurgeryAgent(max_retries=2, wait=1)
        odontology = OdontologyAgent(max_retries=2, wait=1)
        obstetrics = ObstetricsAgent(max_retries=2, wait=1)
        dermatology = DermatologyAgent(max_retries=2, wait=1)
        psychiatry = PsychiatryAgent(max_retries=2, wait=1)
        
        # Layer 3: LightRAG Retrieval
        retrieve = RetrieveFromKBWithDemuc()
        
        # Layer 4: Output
        compose = ComposeAnswer()
        fallback = FallbackNode()
        
        # Layer 5: Memory
        memory_manager = MemoryManager(max_retries=3)
        add_memory = AddMemory(max_retries=3)
        update_memory = UpdateMemory(max_retries=3)
        delete_memory = DeleteMemory(max_retries=3)

        # =============================================
        # 2. DEFINE FLOW EDGES
        # =============================================
        
        # Layer 1 → Layer 2: Cognitive pipeline
        ingest >> state_manager >> master_router

        # Layer 2 → Layer 3: Specialist routing (9 routes)
        master_router - "noi_khoa" >> internal_med
        internal_med >> retrieve

        master_router - "nhi_khoa" >> pediatrics
        pediatrics >> retrieve

        master_router - "duoc_ly" >> pharmacology
        pharmacology >> retrieve

        master_router - "ngoai_khoa" >> surgery
        surgery >> retrieve

        master_router - "nha_khoa" >> odontology
        odontology >> retrieve

        master_router - "san_khoa" >> obstetrics
        obstetrics >> retrieve

        master_router - "da_lieu" >> dermatology
        dermatology >> retrieve

        master_router - "tam_than" >> psychiatry
        psychiatry >> retrieve

        # Layer 3 → Layer 4: All specialists → Retrieve → Compose
        retrieve >> compose
        
        # Chitchat → Compose directly (skip specialists + retrieval)
        master_router - "chitchat" >> compose

        # Layer 4 → Layer 5: Compose → Memory management
        compose >> memory_manager
        
        # Memory chain
        memory_manager - "default" >> add_memory >> update_memory >> delete_memory
        memory_manager - "skip" >> None

        # Fallback routes for error handling
        state_manager - "fallback" >> fallback
        master_router - "fallback" >> fallback
        retrieve - "fallback" >> fallback
        compose - "fallback" >> fallback

        # =============================================
        # 3. SET START NODE
        # =============================================
        super().__init__(start=ingest)
