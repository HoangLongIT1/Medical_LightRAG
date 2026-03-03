# core/nodes/ClinicalStateManager.py
"""
Clinical State Manager (Layer 1 - Cognitive Layer)

This node is responsible for:
1. Loading chat history from PostgreSQL (via thread_id)
2. Loading the previous clinical state from the clinical_states table
3. Extracting symptoms, profile, and intent from the conversation via LLM
4. Comparing old vs new symptoms (added / removed / unchanged)
5. Persisting the updated clinical state back to PostgreSQL
6. Setting shared["clinical_state"] and shared["intent"] for downstream routing
"""

from pocketflow import Node
import logging
import json

from utils.llm import call_llm
from utils.parsing.response_parser import parse_json_from_llm
from utils.llm.prompts_advanced import CLINICAL_STATE_PROMPT
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
# Symptom Comparison Logic
# ============================================================================

def compare_symptoms(old_symptoms: list, new_symptoms: list) -> dict:
    """
    Compare old and new symptom lists to produce a structured diff.
    
    Uses normalized string matching (lowercased, stripped) to handle
    minor variations in symptom descriptions.
    
    Returns:
        {
            "added": ["symptom3"],      # New symptoms not in old
            "removed": ["symptom1"],    # Old symptoms no longer present
            "unchanged": ["symptom2"],  # Symptoms present in both
            "has_changes": True/False   # Quick flag
        }
    """
    # Normalize for comparison (lowercase, strip whitespace)
    def normalize(s):
        return s.strip().lower() if isinstance(s, str) else str(s).strip().lower()
    
    old_set = {normalize(s) for s in old_symptoms}
    new_set = {normalize(s) for s in new_symptoms}
    
    # Compute diff
    added_normalized = new_set - old_set
    removed_normalized = old_set - new_set
    unchanged_normalized = old_set & new_set
    
    # Map back to original strings (prefer new version for display)
    old_map = {normalize(s): s for s in old_symptoms}
    new_map = {normalize(s): s for s in new_symptoms}
    
    added = [new_map[n] for n in added_normalized if n in new_map]
    removed = [old_map[n] for n in removed_normalized if n in old_map]
    unchanged = [new_map.get(n, old_map.get(n, n)) for n in unchanged_normalized]
    
    return {
        "added": added,
        "removed": removed,
        "unchanged": unchanged,
        "has_changes": bool(added or removed),
    }


# ============================================================================
# Database Operations
# ============================================================================

def load_chat_history_from_db(thread_id: str, limit: int = 20) -> list:
    """
    Load recent chat messages from PostgreSQL for the given thread.
    
    Returns list of dicts: [{"role": "user"/"bot", "content": "..."}, ...]
    """
    if not thread_id:
        return []
    
    try:
        from database.db import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        try:
            result = db.execute(
                text("""
                    SELECT role, content 
                    FROM chat_messages 
                    WHERE thread_id = :tid 
                    ORDER BY timestamp DESC 
                    LIMIT :lim
                """),
                {"tid": thread_id, "lim": limit}
            )
            rows = result.fetchall()
            # Reverse to get chronological order (oldest first)
            messages = [{"role": row[0], "content": row[1]} for row in reversed(rows)]
            logger.info(f"📋 [ClinicalState] Loaded {len(messages)} messages from thread {thread_id[:8]}...")
            return messages
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ [ClinicalState] Error loading chat history: {e}")
        return []


def load_clinical_state_from_db(thread_id: str) -> dict:
    """
    Load the previous clinical state from PostgreSQL.
    Returns default state if none exists.
    """
    default_state = {
        "profile": {},
        "symptoms": [],
        "previous_symptoms": [],
        "current_condition": "",
        "symptom_changes": {},
        "intent": "UNKNOWN",
    }
    
    if not thread_id:
        return default_state
    
    try:
        from database.db import SessionLocal
        from database.models import ClinicalState
        
        db = SessionLocal()
        try:
            state = db.query(ClinicalState).filter(
                ClinicalState.thread_id == thread_id
            ).first()
            
            if state:
                logger.info(f"📋 [ClinicalState] Loaded existing state for thread {thread_id[:8]}...")
                return {
                    "profile": state.profile or {},
                    "symptoms": state.symptoms or [],
                    "previous_symptoms": state.previous_symptoms or [],
                    "current_condition": state.current_condition or "",
                    "symptom_changes": state.symptom_changes or {},
                    "intent": state.intent or "UNKNOWN",
                }
            else:
                logger.info(f"📋 [ClinicalState] No existing state for thread {thread_id[:8]}, using defaults")
                return default_state
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ [ClinicalState] Error loading clinical state: {e}")
        return default_state


def save_clinical_state_to_db(thread_id: str, state: dict):
    """
    Persist the updated clinical state to PostgreSQL.
    Uses upsert — inserts if not exists, updates if exists.
    """
    if not thread_id:
        logger.warning("⚠️ [ClinicalState] No thread_id, skipping DB save")
        return
    
    try:
        from database.db import SessionLocal
        from database.models import ClinicalState
        
        db = SessionLocal()
        try:
            existing = db.query(ClinicalState).filter(
                ClinicalState.thread_id == thread_id
            ).first()
            
            if existing:
                # Update existing record
                existing.symptoms = state.get("symptoms", [])
                existing.previous_symptoms = state.get("previous_symptoms", [])
                existing.profile = state.get("profile", {})
                existing.current_condition = state.get("current_condition", "")
                existing.symptom_changes = state.get("symptom_changes", {})
                existing.intent = state.get("intent", "UNKNOWN")
                logger.info(f"✅ [ClinicalState] Updated state for thread {thread_id[:8]}")
            else:
                # Insert new record
                new_state = ClinicalState(
                    thread_id=thread_id,
                    symptoms=state.get("symptoms", []),
                    previous_symptoms=state.get("previous_symptoms", []),
                    profile=state.get("profile", {}),
                    current_condition=state.get("current_condition", ""),
                    symptom_changes=state.get("symptom_changes", {}),
                    intent=state.get("intent", "UNKNOWN"),
                )
                db.add(new_state)
                logger.info(f"✅ [ClinicalState] Created state for thread {thread_id[:8]}")
            
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"❌ [ClinicalState] Error saving state: {e}")
            raise
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ [ClinicalState] DB save failed: {e}")


# ============================================================================
# ClinicalStateManager Node
# ============================================================================

class ClinicalStateManager(Node):
    """
    Clinical State Manager (Layer 1 - Cognitive Layer)
    
    Flow: prep() → exec() → post()
    
    prep():
        - Load user input and thread_id from shared
        - Load chat history from PostgreSQL
        - Load previous clinical state from PostgreSQL
    
    exec():
        - Call LLM to extract/update symptoms, profile, intent
        - Compare old vs new symptoms (structured diff)
    
    post():
        - Save updated state to PostgreSQL
        - Write clinical_state and intent to shared for MasterMedicalRouter
    """
    
    def __init__(self, max_retries=2, wait=1):
        super().__init__(max_retries=max_retries, wait=wait)

    def prep(self, shared):
        user_input = shared.get("input", "")
        thread_id = shared.get("thread_id", "")
        
        # 1. Load chat history from PostgreSQL
        chat_history = load_chat_history_from_db(thread_id)
        
        # 2. Load previous clinical state from PostgreSQL
        previous_state = load_clinical_state_from_db(thread_id)
        
        logger.info(f"📝 [ClinicalState] PREP - Thread: {thread_id[:8] if thread_id else 'N/A'}, "
                     f"History: {len(chat_history)} msgs, "
                     f"Previous symptoms: {previous_state.get('symptoms', [])}")
        
        return {
            "user_input": user_input,
            "thread_id": thread_id,
            "chat_history": chat_history,
            "previous_state": previous_state,
        }

    def exec(self, inputs):
        user_input = inputs["user_input"]
        chat_history = inputs["chat_history"]
        previous_state = inputs["previous_state"]
        old_symptoms = previous_state.get("symptoms", [])
        
        # Format chat history for the prompt
        history_text = ""
        if chat_history:
            lines = []
            for msg in chat_history[-10:]:  # Last 10 messages for context
                role_label = "Bệnh nhân" if msg["role"] == "user" else "Hệ thống"
                lines.append(f"  - {role_label}: {msg['content'][:200]}")
            history_text = "\n".join(lines)
        
        # Build the LLM prompt
        prompt = CLINICAL_STATE_PROMPT.format(
            current_state=json.dumps(previous_state, ensure_ascii=False, indent=2),
            chat_history=history_text or "(Chưa có lịch sử trò chuyện)",
            user_input=user_input,
        )
        
        logger.info(f"📝 [ClinicalState] EXEC - Calling LLM for symptom extraction...")
        
        # Call LLM
        response_str = call_llm(prompt, max_retry_time=timeout_config.LLM_RETRY_TIMEOUT)
        new_state = parse_json_from_llm(response_str)
        
        if not new_state or not isinstance(new_state, dict):
            logger.warning("📝 [ClinicalState] EXEC - LLM returned invalid state, using previous")
            new_state = previous_state.copy()
            new_state["intent"] = "MEDICAL"  # Default to medical
        
        # ============================================================
        # SYMPTOM COMPARISON LOGIC (old vs new)
        # ============================================================
        new_symptoms = new_state.get("symptoms", [])
        symptom_diff = compare_symptoms(old_symptoms, new_symptoms)
        
        # Store the diff and previous symptoms in the state
        new_state["previous_symptoms"] = old_symptoms
        new_state["symptom_changes"] = symptom_diff
        
        # Log the symptom comparison
        if symptom_diff["has_changes"]:
            logger.info(f"🔄 [ClinicalState] SYMPTOM CHANGES DETECTED:")
            if symptom_diff["added"]:
                logger.info(f"   ➕ Added: {symptom_diff['added']}")
            if symptom_diff["removed"]:
                logger.info(f"   ➖ Removed: {symptom_diff['removed']}")
            if symptom_diff["unchanged"]:
                logger.info(f"   ⏸️  Unchanged: {symptom_diff['unchanged']}")
        else:
            logger.info(f"📝 [ClinicalState] No symptom changes detected")
        
        logger.info(f"📝 [ClinicalState] EXEC - Condition: {new_state.get('current_condition', 'N/A')}")
        logger.info(f"📝 [ClinicalState] EXEC - Intent: {new_state.get('intent', 'UNKNOWN')}")
        
        return {
            "state": new_state,
            "thread_id": inputs["thread_id"],
        }

    def post(self, shared, prep_res, exec_res):
        # Handle failure
        if exec_res is None:
            logger.error("📝 [ClinicalState] POST - exec_res is None, using fallback")
            shared["clinical_state"] = {
                "profile": {},
                "symptoms": [],
                "current_condition": "",
                "intent": "MEDICAL",
                "symptom_changes": {"added": [], "removed": [], "unchanged": [], "has_changes": False},
            }
            shared["intent"] = "MEDICAL"
            return "default"
        
        new_state = exec_res["state"]
        thread_id = exec_res["thread_id"]
        
        # 1. Persist to PostgreSQL
        save_clinical_state_to_db(thread_id, new_state)
        
        # 2. Write to shared store for downstream nodes
        shared["clinical_state"] = new_state
        shared["intent"] = new_state.get("intent", "MEDICAL")
        
        # 3. Also set symptom_changes for compose answer to reference
        shared["symptom_changes"] = new_state.get("symptom_changes", {})
        
        logger.info(f"📝 [ClinicalState] POST - State saved. Intent: {shared['intent']}")
        
        return "default"