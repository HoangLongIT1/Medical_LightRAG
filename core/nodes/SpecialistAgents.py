# core/nodes/SpecialistAgents.py
"""
Specialist Agents (Layer 3 - Execution Layer)

Five specialist nodes that rewrite the user's query with domain-specific 
medical context before routing to LightRAG for retrieval.

Each agent:
- prep(): Reads clinical_state, query, and symptom_changes from shared
- exec(): Calls LLM with a specialty-specific prompt to optimize the query
- post(): Sets shared["retrieval_query"] (rewritten) and shared["specialist_context"]
"""

from pocketflow import Node
import logging
import json

from utils.llm import call_llm
from utils.parsing.response_parser import parse_json_from_llm
from utils.llm.prompts_advanced import (
    INTERNAL_MEDICINE_PROMPT,
    PEDIATRICS_PROMPT,
    PHARMACOLOGY_PROMPT,
    SURGERY_PROMPT,
    ODONTOLOGY_PROMPT,
    OBSTETRICS_PROMPT,
    DERMATOLOGY_PROMPT,
    PSYCHIATRY_PROMPT,
)
from config.timeout_config import timeout_config

# Configure logging
from utils.timezone_utils import setup_vietnam_logging
from config.logging_config import logging_config

if logging_config.USE_VIETNAM_TIMEZONE:
    logger = setup_vietnam_logging(__name__,
                                 level=getattr(logging, logging_config.LOG_LEVEL.upper()),
                                 format_str=logging_config.LOG_FORMAT)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, logging_config.LOG_LEVEL.upper()))


# ============================================================================
# Base Specialist Agent
# ============================================================================

class BaseSpecialistAgent(Node):
    """Base class for all specialist agents.
    
    Subclasses must set:
        - specialist_name: Display name for logging
        - prompt_template: The prompt string with {clinical_state}, {query}, {symptom_changes}
    """
    specialist_name = "Base"
    prompt_template = ""

    def __init__(self, max_retries=2, wait=1):
        super().__init__(max_retries=max_retries, wait=wait)

    def prep(self, shared):
        clinical_state = shared.get("clinical_state", {})
        query = shared.get("retrieval_query") or shared.get("query", "")
        symptom_changes = shared.get("symptom_changes", {})

        logger.info(f"🏥 [{self.specialist_name}] PREP - Query: '{query[:60]}...'")

        return {
            "clinical_state": clinical_state,
            "query": query,
            "symptom_changes": symptom_changes,
        }

    def exec(self, inputs):
        clinical_state = inputs["clinical_state"]
        query = inputs["query"]
        symptom_changes = inputs["symptom_changes"]

        # Build prompt using the specialist's template
        prompt = self.prompt_template.format(
            clinical_state=json.dumps(clinical_state, ensure_ascii=False, indent=2),
            query=query,
            symptom_changes=json.dumps(symptom_changes, ensure_ascii=False),
        )

        logger.info(f"🏥 [{self.specialist_name}] EXEC - Calling LLM for query optimization...")

        response_str = call_llm(prompt, max_retry_time=timeout_config.LLM_RETRY_TIMEOUT)
        result = parse_json_from_llm(response_str)

        if not result or not isinstance(result, dict):
            logger.warning(f"🏥 [{self.specialist_name}] EXEC - LLM returned invalid JSON, using original query")
            result = {
                "specialist_analysis": "",
                "optimized_query": query,
            }

        logger.info(f"🏥 [{self.specialist_name}] EXEC - Optimized query: '{result.get('optimized_query', query)[:80]}...'")
        logger.info(f"🏥 [{self.specialist_name}] EXEC - Analysis: {result.get('specialist_analysis', 'N/A')[:100]}")

        return result

    def post(self, shared, prep_res, exec_res):
        if exec_res is None:
            logger.error(f"🏥 [{self.specialist_name}] POST - exec_res is None, using original query")
            return "default"

        # Set the optimized retrieval query for RetrieveFromKBWithDemuc
        optimized_query = exec_res.get("optimized_query", "")
        if optimized_query:
            shared["retrieval_query"] = optimized_query
        
        # Store specialist analysis context for ComposeAnswer
        shared["specialist_context"] = {
            "specialist": self.specialist_name,
            "analysis": exec_res.get("specialist_analysis", ""),
            "extra": {k: v for k, v in exec_res.items() 
                     if k not in ("specialist_analysis", "optimized_query")},
        }

        logger.info(f"🏥 [{self.specialist_name}] POST - retrieval_query updated, specialist_context set")

        return "default"


# ============================================================================
# Internal Medicine Agent (Nội Khoa)
# ============================================================================

class InternalMedicineAgent(BaseSpecialistAgent):
    """
    Internal Medicine Specialist (Nội Khoa).
    
    Handles: Cardiovascular, respiratory, GI, renal, endocrine, 
    neurological, musculoskeletal conditions.
    """
    specialist_name = "Nội Khoa"
    prompt_template = INTERNAL_MEDICINE_PROMPT


# ============================================================================
# Pediatrics Agent (Nhi Khoa)
# ============================================================================

class PediatricsAgent(BaseSpecialistAgent):
    """
    Pediatrics Specialist (Nhi Khoa).
    
    Handles: Child-specific diseases, dosing by weight, 
    vaccination schedules, growth & development.
    """
    specialist_name = "Nhi Khoa"
    prompt_template = PEDIATRICS_PROMPT


# ============================================================================
# Pharmacology Agent (Dược Lý)
# ============================================================================

class PharmacologyAgent(BaseSpecialistAgent):
    """
    Clinical Pharmacologist (Dược Lý).
    
    Handles: Drug interactions, dosing, contraindications,
    side effects, special populations.
    """
    specialist_name = "Dược Lý"
    prompt_template = PHARMACOLOGY_PROMPT


# ============================================================================
# Surgery Agent (Ngoại Khoa)
# ============================================================================

class SurgeryAgent(BaseSpecialistAgent):
    """
    General & Trauma Surgeon (Ngoại Khoa).
    
    Handles: Trauma (fractures, dislocations, lacerations), 
    general surgery (appendicitis, hernia, bowel obstruction),
    burns, perioperative care, surgical emergencies.
    """
    specialist_name = "Ngoại Khoa"
    prompt_template = SURGERY_PROMPT


# ============================================================================
# Odontology Agent (Nha Khoa)
# ============================================================================

class OdontologyAgent(BaseSpecialistAgent):
    """
    Dental & Maxillofacial Specialist (Nha Khoa / Răng Hàm Mặt).
    
    Handles: Dental caries, periodontal disease, oral surgery,
    orthodontics, prosthodontics, endodontics, pediatric dentistry,
    oral mucosal diseases.
    """
    specialist_name = "Nha Khoa"
    prompt_template = ODONTOLOGY_PROMPT


# ============================================================================
# Obstetrics Agent (Sản Khoa)
# ============================================================================

class ObstetricsAgent(BaseSpecialistAgent):
    """
    Obstetrician & Gynecologist (Sản Khoa).
    
    Handles: Pregnancy care, labor & delivery, postpartum,
    gynecological conditions, medication safety in pregnancy.
    """
    specialist_name = "Sản Khoa"
    prompt_template = OBSTETRICS_PROMPT


# ============================================================================
# Dermatology Agent (Đa Liễu)
# ============================================================================

class DermatologyAgent(BaseSpecialistAgent):
    """
    Dermatologist (Đa Liễu).
    
    Handles: Skin infections, eczema, psoriasis, allergies,
    acne, skin tumors, hair & nail diseases.
    """
    specialist_name = "Đa Liễu"
    prompt_template = DERMATOLOGY_PROMPT


# ============================================================================
# Psychiatry Agent (Tâm Thần)
# ============================================================================

class PsychiatryAgent(BaseSpecialistAgent):
    """
    Psychiatrist (Tâm Thần).
    
    Handles: Depression, anxiety, sleep disorders, psychosis,
    eating disorders, substance abuse, stress & burnout.
    
    NOTE: This specialist has additional safety considerations.
    Crisis hotline: 1800 599 100
    """
    specialist_name = "Tâm Thần"
    prompt_template = PSYCHIATRY_PROMPT
