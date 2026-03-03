"""Verify all new components import and work correctly."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("VERIFICATION TESTS")
print("=" * 60)

# Test 1: Database model
print("\n--- Test 1: ClinicalState model ---")
from database.models import ClinicalState
print(f"✅ ClinicalState model: {ClinicalState.__tablename__}")
print(f"   Columns: {[c.name for c in ClinicalState.__table__.columns]}")

# Test 2: Symptom comparison logic
print("\n--- Test 2: Symptom comparison logic ---")
from core.nodes.ClinicalStateManager import compare_symptoms

# Case A: New symptoms added
diff1 = compare_symptoms(
    old_symptoms=["đau đầu", "sốt"],
    new_symptoms=["đau đầu", "sốt", "buồn nôn"]
)
assert diff1["added"] == ["buồn nôn"], f"Expected ['buồn nôn'], got {diff1['added']}"
assert diff1["removed"] == [], f"Expected [], got {diff1['removed']}"
assert diff1["has_changes"] == True
print(f"✅ Case A (add): added={diff1['added']}, removed={diff1['removed']}")

# Case B: Symptom removed (patient says it's gone)
diff2 = compare_symptoms(
    old_symptoms=["đau đầu", "sốt", "buồn nôn"],
    new_symptoms=["sốt", "buồn nôn"]
)
assert diff2["removed"] == ["đau đầu"], f"Expected ['đau đầu'], got {diff2['removed']}"
assert diff2["has_changes"] == True
print(f"✅ Case B (remove): added={diff2['added']}, removed={diff2['removed']}")

# Case C: Symptom replaced (patient corrects)
diff3 = compare_symptoms(
    old_symptoms=["đau đầu"],
    new_symptoms=["đau bụng"]
)
assert "đau đầu" in diff3["removed"]
assert "đau bụng" in diff3["added"]
assert len(diff3["unchanged"]) == 0
print(f"✅ Case C (replace): added={diff3['added']}, removed={diff3['removed']}")

# Case D: No changes
diff4 = compare_symptoms(
    old_symptoms=["đau đầu", "sốt"],
    new_symptoms=["sốt", "đau đầu"]  # Same symptoms, different order
)
assert diff4["has_changes"] == False
print(f"✅ Case D (no change): has_changes={diff4['has_changes']}")

# Case E: Empty to new
diff5 = compare_symptoms(
    old_symptoms=[],
    new_symptoms=["đau ngực", "khó thở"]
)
assert len(diff5["added"]) == 2
assert len(diff5["removed"]) == 0
print(f"✅ Case E (first visit): added={diff5['added']}")

# Test 3: DB operations
print("\n--- Test 3: Database operations ---")
from core.nodes.ClinicalStateManager import (
    load_clinical_state_from_db,
    save_clinical_state_to_db,
    load_chat_history_from_db,
)
state = load_clinical_state_from_db("nonexistent-thread")
print(f"✅ Load non-existent state: {state['intent']} (default)")

# Test 4: Node imports
print("\n--- Test 4: All node imports ---")
from core.nodes import (
    ClinicalStateManager,
    MasterMedicalRouter,
    InternalMedicineAgent,
    PediatricsAgent,
    PharmacologyAgent,
)
print(f"✅ ClinicalStateManager: {ClinicalStateManager}")
print(f"✅ MasterMedicalRouter: {MasterMedicalRouter}")
print(f"✅ InternalMedicineAgent: {InternalMedicineAgent}")
print(f"✅ PediatricsAgent: {PediatricsAgent}")
print(f"✅ PharmacologyAgent: {PharmacologyAgent}")

# Test 5: Flow import
print("\n--- Test 5: AdvancedMedicalFlow ---")
from core.flows.advanced_medical_flow import AdvancedMedicalFlow
flow = AdvancedMedicalFlow()
print(f"✅ AdvancedMedicalFlow created: {type(flow)}")
print(f"   Start node: {type(flow.start_node).__name__}")

# Test 6: Prompts
print("\n--- Test 6: Prompts ---")
from utils.llm.prompts_advanced import (
    CLINICAL_STATE_PROMPT,
    MASTER_ROUTER_PROMPT,
    INTERNAL_MEDICINE_PROMPT,
    PEDIATRICS_PROMPT,
    PHARMACOLOGY_PROMPT,
)
print(f"✅ CLINICAL_STATE_PROMPT: {len(CLINICAL_STATE_PROMPT)} chars")
print(f"✅ MASTER_ROUTER_PROMPT: {len(MASTER_ROUTER_PROMPT)} chars")
print(f"✅ INTERNAL_MEDICINE_PROMPT: {len(INTERNAL_MEDICINE_PROMPT)} chars")
print(f"✅ PEDIATRICS_PROMPT: {len(PEDIATRICS_PROMPT)} chars")
print(f"✅ PHARMACOLOGY_PROMPT: {len(PHARMACOLOGY_PROMPT)} chars")

# Test 7: App import
print("\n--- Test 7: FastAPI app ---")
from app import app
print(f"✅ App imported: {app.title} v{app.version}")
routes = [r.path for r in app.routes if hasattr(r, 'path')]
lightrag_routes = [r for r in routes if 'lightrag' in r]
print(f"✅ Total routes: {len(routes)}")
print(f"✅ LightRAG routes: {lightrag_routes}")

print("\n" + "=" * 60)
print("ALL TESTS PASSED ✅")
print("=" * 60)
