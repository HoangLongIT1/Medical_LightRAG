# core/nodes/MasterMedicalRouter.py
"""
Master Medical Router (Layer 2 - Routing & Safety)

Routes user queries to the appropriate specialist agent based on
clinical state analysis. Supports 4 routes:

- "chitchat"  → ComposeAnswer (skip medical logic)
- "noi_khoa"  → InternalMedicineAgent
- "nhi_khoa"  → PediatricsAgent
- "duoc_ly"   → PharmacologyAgent
"""

from pocketflow import Node
import logging
import json

from utils.llm import call_llm
from utils.llm.prompts_advanced import MASTER_ROUTER_PROMPT
from utils.parsing.response_parser import parse_json_from_llm
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


# Valid specialist routes
VALID_SPECIALISTS = {"noi_khoa", "nhi_khoa", "duoc_ly", "ngoai_khoa", "nha_khoa", "san_khoa", "da_lieu", "tam_than"}


class MasterMedicalRouter(Node):
    """
    Routes to specialist agents or chitchat based on clinical state + intent.
    
    prep(): Read intent and clinical_state from shared
    exec(): If MEDICAL, call LLM to determine specialist; if CHITCHAT, skip
    post(): Return route action string for flow wiring
    """
    
    def __init__(self, max_retries=2, wait=1):
        super().__init__(max_retries=max_retries, wait=wait)

    def prep(self, shared):
        intent = shared.get("intent", "MEDICAL")
        clinical_state = shared.get("clinical_state", {})
        query = shared.get("query", "")
        
        logger.info(f"👨‍⚕️ [MasterRouter] PREP - Intent: {intent}, Query: '{query[:60]}...'")
        
        return {
            "intent": intent,
            "clinical_state": clinical_state,
            "query": query,
        }

    def exec(self, inputs):
        intent = inputs["intent"]
        clinical_state = inputs["clinical_state"]
        query = inputs["query"]
        
        # Fast path: chitchat doesn't need specialist analysis
        if intent == "CHITCHAT":
            logger.info("👨‍⚕️ [MasterRouter] EXEC - Chitchat detected, skipping specialist routing")
            return {"route": "chitchat", "search_query": query}
        
        # Medical path: determine specialist via LLM
        prompt = MASTER_ROUTER_PROMPT.format(
            clinical_state=json.dumps(clinical_state, ensure_ascii=False, indent=2)
        )
        
        logger.info("👨‍⚕️ [MasterRouter] EXEC - Calling LLM for specialist routing...")
        
        response_str = call_llm(prompt, max_retry_time=timeout_config.LLM_RETRY_TIMEOUT)
        router_output = parse_json_from_llm(response_str)
        
        if not router_output or not isinstance(router_output, dict):
            logger.warning("👨‍⚕️ [MasterRouter] EXEC - Invalid LLM response, defaulting to noi_khoa")
            return {"route": "noi_khoa", "search_query": query}
        
        # Validate specialist
        specialist = router_output.get("primary_specialist", "noi_khoa")
        if specialist not in VALID_SPECIALISTS:
            logger.warning(f"👨‍⚕️ [MasterRouter] EXEC - Invalid specialist '{specialist}', defaulting to noi_khoa")
            specialist = "noi_khoa"
        
        search_query = router_output.get("search_query", query)
        reason = router_output.get("reason", "")
        
        logger.info(f"👨‍⚕️ [MasterRouter] EXEC - Routing to: {specialist}")
        logger.info(f"👨‍⚕️ [MasterRouter] EXEC - Reason: {reason}")
        logger.info(f"👨‍⚕️ [MasterRouter] EXEC - Search query: '{search_query[:80]}...'")
        
        return {
            "route": specialist,
            "search_query": search_query,
            "reason": reason,
        }

    def post(self, shared, prep_res, exec_res):
        if exec_res is None:
            logger.error("👨‍⚕️ [MasterRouter] POST - exec_res is None, defaulting to noi_khoa")
            shared["retrieval_query"] = shared.get("query", "")
            return "noi_khoa"
        
        # Set the initial retrieval query (specialist will refine further)
        shared["retrieval_query"] = exec_res.get("search_query", shared.get("query", ""))
        shared["routing_reason"] = exec_res.get("reason", "")
        
        route = exec_res.get("route", "noi_khoa")
        logger.info(f"👨‍⚕️ [MasterRouter] POST - Route decision: '{route}'")
        
        return route