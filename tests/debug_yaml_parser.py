"""
Debug script để test từng bước của YAML parser
"""

import re
import yaml
import logging
from utils.response_parser import parse_yaml_response, _extract_from_code_fences

# Setup logging để xem chi tiết
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_code_fence_extraction():
    """Debug the code fence extraction step by step"""
    print("=== DEBUG: Code Fence Extraction ===")
    
    # Test input giống như trong test
    response = """
    Here is the classification:
    ```yaml
    type: medical_question
    confidence: high
    reason: Contains medical terms
    ```
    """
    
    print(f"Input response:\n{repr(response)}")
    print(f"Input response (pretty):\n{response}")
    
    # Use the actual function from response_parser
    yaml_content = _extract_from_code_fences(response)
    if yaml_content:
        print(f"✅ Code fence extraction successful!")
        print(f"Extracted content: {repr(yaml_content)}")
        print(f"Content:\n{yaml_content}")
        
        # Test YAML parsing
        try:
            result = yaml.safe_load(yaml_content)
            print(f"✅ YAML parsing successful: {result}")
            print(f"Is dict: {isinstance(result, dict)}")
            return result
        except Exception as e:
            print(f"❌ YAML parsing failed: {e}")
    else:
        print("❌ Code fence extraction failed")
    
    return None

def debug_full_response_parsing():
    """Debug parsing entire response as YAML"""
    print("\n=== DEBUG: Full Response Parsing ===")
    
    response = """
    Here is the classification:
    ```yaml
    type: medical_question
    confidence: high
    reason: Contains medical terms
    ```
    """
    
    try:
        result = yaml.safe_load(response)
        print(f"✅ Full response YAML parsing: {result}")
        print(f"Is dict: {isinstance(result, dict)}")
        return result
    except Exception as e:
        print(f"❌ Full response YAML parsing failed: {e}")
        return None

def debug_json_fallback():
    """Debug JSON fallback"""
    print("\n=== DEBUG: JSON Fallback ===")
    
    response = """
    Here is the classification:
    ```yaml
    type: medical_question
    confidence: high
    reason: Contains medical terms
    ```
    """
    
    try:
        import json
        result = json.loads(response)
        print(f"✅ JSON parsing: {result}")
        return result
    except Exception as e:
        print(f"❌ JSON parsing failed: {e}")
        return None

def main():
    print("🔍 Debugging YAML Parser Step by Step")
    
    # Test input giống như trong test
    response = """
    Here is the classification:
    ```yaml
    type: medical_question
    confidence: high
    reason: Contains medical terms
    ```
    """
    
    print("=== Testing the actual parse_yaml_response function ===")
    result = parse_yaml_response(response)
    print(f"Final result: {result}")
    
    if result:
        print(f"\n🎉 SUCCESS: {result}")
    else:
        print("\n❌ FAILED - now let's debug step by step")
        
        # Test each strategy
        result1 = debug_code_fence_extraction()
        if result1:
            print(f"\n🎉 SUCCESS with code fence extraction: {result1}")
            return
        
        result2 = debug_full_response_parsing()
        if result2:
            print(f"\n🎉 SUCCESS with full response parsing: {result2}")
            return
        
        result3 = debug_json_fallback()
        if result3:
            print(f"\n🎉 SUCCESS with JSON fallback: {result3}")
            return
        
        print("\n❌ All strategies failed - this matches the test failure!")

if __name__ == "__main__":
    main()
