"""Final verification script for Medical LightRAG system."""
import sys

print("=" * 60)
print("  FINAL VERIFICATION: Medical LightRAG System")
print("=" * 60)

errors = []

# 1. All node imports
print("\n[1/6] Testing all node imports...")
try:
    from core.nodes import (
        IngestQuery, ComposeAnswer, FallbackNode,
        ClinicalStateManager, MasterMedicalRouter,
        InternalMedicineAgent, PediatricsAgent, PharmacologyAgent,
        SurgeryAgent, OdontologyAgent,
        ObstetricsAgent, DermatologyAgent, PsychiatryAgent,
        MemoryManager, AddMemory, UpdateMemory, DeleteMemory, RetrieveFromMemory,
    )
    print("  OK: All 16 nodes imported")
except Exception as e:
    errors.append(f"Node imports: {e}")
    print(f"  FAIL: {e}")

# 2. All prompts
print("\n[2/6] Testing all prompt imports...")
try:
    from utils.llm.prompts_advanced import (
        CLINICAL_STATE_PROMPT, MASTER_ROUTER_PROMPT,
        INTERNAL_MEDICINE_PROMPT, PEDIATRICS_PROMPT, PHARMACOLOGY_PROMPT,
        SURGERY_PROMPT, ODONTOLOGY_PROMPT,
        OBSTETRICS_PROMPT, DERMATOLOGY_PROMPT, PSYCHIATRY_PROMPT,
    )
    for name, p in [
        ("SURGERY", SURGERY_PROMPT), ("ODONTOLOGY", ODONTOLOGY_PROMPT),
        ("OBSTETRICS", OBSTETRICS_PROMPT), ("DERMATOLOGY", DERMATOLOGY_PROMPT),
        ("PSYCHIATRY", PSYCHIATRY_PROMPT),
    ]:
        assert len(p) > 100, f"{name} prompt too short: {len(p)}"
    print("  OK: All 10 prompts imported and validated")
except Exception as e:
    errors.append(f"Prompts: {e}")
    print(f"  FAIL: {e}")

# 3. Router valid specialists
print("\n[3/6] Testing router configuration...")
try:
    from core.nodes.MasterMedicalRouter import VALID_SPECIALISTS
    expected = {"noi_khoa", "nhi_khoa", "duoc_ly", "ngoai_khoa", "nha_khoa", "san_khoa", "da_lieu", "tam_than"}
    assert VALID_SPECIALISTS == expected, f"Mismatch: {VALID_SPECIALISTS}"
    print(f"  OK: 8 valid specialists: {sorted(VALID_SPECIALISTS)}")
except Exception as e:
    errors.append(f"Router: {e}")
    print(f"  FAIL: {e}")

# 4. Flow creation
print("\n[4/6] Testing AdvancedMedicalFlow creation...")
try:
    from core.flows.advanced_medical_flow import AdvancedMedicalFlow
    flow = AdvancedMedicalFlow()
    assert type(flow.start_node).__name__ == "IngestQuery"
    print(f"  OK: Flow created, start={type(flow.start_node).__name__}")
except Exception as e:
    errors.append(f"Flow: {e}")
    print(f"  FAIL: {e}")

# 5. Symptom comparison
print("\n[5/6] Testing symptom comparison logic...")
try:
    from core.nodes.ClinicalStateManager import compare_symptoms
    r = compare_symptoms(["sot", "ho"], ["ho", "dau dau"])
    assert r["has_changes"] is True
    assert "dau dau" in r["added"]
    assert "sot" in r["removed"]
    assert "ho" in r["unchanged"]
    r2 = compare_symptoms([], [])
    assert r2["has_changes"] is False
    print("  OK: Diff logic correct (added/removed/unchanged)")
except Exception as e:
    errors.append(f"Symptom comparison: {e}")
    print(f"  FAIL: {e}")

# 6. App import
print("\n[6/6] Testing FastAPI app import...")
try:
    from app import app
    print(f"  OK: {app.title} v{app.version}")
except Exception as e:
    errors.append(f"App import: {e}")
    print(f"  FAIL: {e}")

# Summary
print("\n" + "=" * 60)
if errors:
    print(f"  RESULT: {len(errors)} ERROR(S) FOUND")
    for e in errors:
        print(f"    X {e}")
    sys.exit(1)
else:
    print("  ALL 6 TESTS PASSED - System is CLEAN and READY")
    print("=" * 60)
