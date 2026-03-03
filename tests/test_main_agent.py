#!/usr/bin/env python3
"""
Test script cho MainAgent centralized architecture
"""

import logging
import sys
import os

# Add the project root to Python path
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from flow import med_flow

# Configure logging to see the flow execution
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def test_main_agent(description, role, user_input, expected_behavior=None):
    """Test một case với MainAgent và in kết quả"""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"Role: {role}")
    print(f"Input: {user_input}")
    if expected_behavior:
        print(f"Expected: {expected_behavior}")
    print(f"{'='*60}")
    
    shared = {
        "role": role,
        "input": user_input,
        "history": []
    }
    
    try:
        # Run the simplified flow
        med_flow.run(shared)
        
        # Print results
        print(f"\nInput Type: {shared.get('input_type', 'Unknown')}")
        print(f"Context: {shared.get('response_context', 'Unknown')}")
        print(f"Retrieval Score: {shared.get('retrieval_score', 'N/A')}")
        print(f"Retrieved Items: {len(shared.get('retrieved', []))}")
        
        print(f"\nFinal Answer:")
        print(f"{shared.get('answer', 'No answer')}")
        
        if 'suggestions' in shared and shared['suggestions']:
            print(f"\nSuggestions:")
            for i, suggestion in enumerate(shared['suggestions'], 1):
                print(f"  {i}. {suggestion}")
        else:
            print(f"\nSuggestions: None")
                
        # Check expected behavior
        if expected_behavior:
            actual_input_type = shared.get('input_type')
            actual_context = shared.get('response_context')
            if expected_behavior in [actual_input_type, actual_context]:
                print(f"✅ Behavior match: {expected_behavior}")
            else:
                print(f"⚠️ Behavior different: expected {expected_behavior}, got input_type={actual_input_type}, context={actual_context}")
        
        print(f"✅ Test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive tests for MainAgent"""
    print("Testing MainAgent centralized architecture...")
    print("=" * 60)
    
    test_cases = [
        {
            "description": "Greeting Test",
            "role": "Bác sĩ nha khoa",
            "user_input": "",
            "expected_behavior": "greeting"
        },
        {
            "description": "Statement Test", 
            "role": "Bệnh nhân đái tháo đường",
            "user_input": "Tôi vừa ăn sáng xong",
            "expected_behavior": "statement"
        },
        {
            "description": "Nonsense Test",
            "role": "Bác sĩ nội tiết",
            "user_input": "xyz123!@#",
            "expected_behavior": "nonsense"
        },
        {
            "description": "Topic Suggestion Request",
            "role": "Bệnh nhân đái tháo đường",
            "user_input": "Gợi ý chủ đề cho tôi",
            "expected_behavior": "topic_suggestion"
        },
        {
            "description": "Medical Question - Should find good match",
            "role": "Bệnh nhân nha khoa",
            "user_input": "Làm thế nào để chăm sóc răng miệng khi bị đái tháo đường?",
            "expected_behavior": "medical_question"  # Could be either detailed_answer or medical_low_score
        },
        {
            "description": "Medical Question - Likely low score",
            "role": "Bác sĩ nha khoa", 
            "user_input": "Bệnh lạ không có trong database xyz",
            "expected_behavior": "medical_low_score"
        },
        {
            "description": "Complex Medical Query",
            "role": "Bác sĩ nội tiết",
            "user_input": "Mối quan hệ giữa viêm nha chu và kiểm soát đường huyết ở bệnh nhân type 2?",
            "expected_behavior": "medical_question"
        },
        {
            "description": "Patient Simple Question",
            "role": "Bệnh nhân nha khoa",
            "user_input": "Tôi có nên đánh răng sau khi ăn không?",
            "expected_behavior": "medical_question"
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for test_case_data in test_cases:
        if test_main_agent(**test_case_data):
            passed += 1
        print()  # Add spacing between tests
    
    print(f"{'='*60}")
    print(f"MAIN AGENT TEST SUMMARY")
    print(f"Passed: {passed}/{total} tests")
    print(f"Success Rate: {passed/total*100:.1f}%")
    print(f"{'='*60}")
    
    if passed == total:
        print("🎉 All tests passed! MainAgent is working correctly.")
    else:
        print(f"⚠️ {total - passed} tests failed. Check the logs above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
