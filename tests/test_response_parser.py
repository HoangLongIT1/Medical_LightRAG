"""
Test script để kiểm tra improved response parser với các edge cases
"""

import logging
from utils.response_parser import (
    parse_yaml_response, 
    validate_yaml_structure, 
    parse_yaml_with_schema,
    safe_size_check
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_yaml_parsing():
    """Test basic YAML parsing functionality"""
    logger.info("=== Test Basic YAML Parsing ===")
    
    # Test 1: Valid YAML with code fence
    response1 = """
    Here is the classification:
    ```yaml
    type: medical_question
    confidence: high
    reason: Contains medical terms
    ```
    """
    
    result1 = parse_yaml_response(response1)
    print(f"Test 1 - Code fence YAML: {result1}")
    assert result1 is not None
    assert result1["type"] == "medical_question"
    
    # Test 2: Valid YAML without code fence
    response2 = """
    type: greeting
    confidence: medium
    """
    
    result2 = parse_yaml_response(response2)
    print(f"Test 2 - Direct YAML: {result2}")
    assert result2 is not None
    assert result2["type"] == "greeting"
    
    # Test 3: JSON fallback
    response3 = '{"type": "statement", "confidence": "low"}'
    
    result3 = parse_yaml_response(response3)
    print(f"Test 3 - JSON fallback: {result3}")
    assert result3 is not None
    assert result3["type"] == "statement"
    
    logger.info("✅ Basic YAML parsing tests passed")


def test_schema_validation():
    """Test schema validation functionality"""
    logger.info("=== Test Schema Validation ===")
    
    # Test 1: Valid structure
    data1 = {"type": "medical_question", "confidence": "high"}
    is_valid1 = validate_yaml_structure(
        data1, 
        required_fields=["type"],
        optional_fields=["confidence"],
        field_types={"type": str, "confidence": str}
    )
    print(f"Test 1 - Valid structure: {is_valid1}")
    assert is_valid1 is True
    
    # Test 2: Missing required field
    data2 = {"confidence": "high"}
    is_valid2 = validate_yaml_structure(
        data2,
        required_fields=["type"]
    )
    print(f"Test 2 - Missing required field: {is_valid2}")
    assert is_valid2 is False
    
    # Test 3: Wrong field type
    data3 = {"type": 123, "confidence": "high"}
    is_valid3 = validate_yaml_structure(
        data3,
        required_fields=["type"],
        field_types={"type": str}
    )
    print(f"Test 3 - Wrong field type: {is_valid3}")
    assert is_valid3 is False
    
    logger.info("✅ Schema validation tests passed")


def test_edge_cases():
    """Test edge cases and error handling"""
    logger.info("=== Test Edge Cases ===")
    
    # Test 1: Empty string
    result1 = parse_yaml_response("")
    print(f"Test 1 - Empty string: {result1}")
    assert result1 is None
    
    # Test 2: None input
    result2 = parse_yaml_response(None)
    print(f"Test 2 - None input: {result2}")
    assert result2 is None
    
    # Test 3: Invalid YAML
    response3 = """
    type: medical_question
    confidence: high
    malformed: [unclosed bracket
    """
    result3 = parse_yaml_response(response3)
    print(f"Test 3 - Invalid YAML: {result3}")
    # Should still try to extract what it can or return None
    
    # Test 4: Very large response (should pass size check for reasonable size)
    large_response = "type: test\ndata: " + "x" * 1000
    result4 = safe_size_check(large_response)
    print(f"Test 4 - Large response size check: {result4}")
    assert result4 is True
    
    # Test 5: Too large response
    too_large = "x" * 60000  # Over 50KB limit
    result5 = safe_size_check(too_large)
    print(f"Test 5 - Too large response: {result5}")
    assert result5 is False
    
    logger.info("✅ Edge case tests passed")


def test_parse_with_schema():
    """Test the combined parse + validate function"""
    logger.info("=== Test Parse with Schema ===")
    
    # Test 1: Valid response with schema
    response1 = """
    ```yaml
    questions:
      - "What are the symptoms?"
      - "How is it treated?"
      - "What causes it?"
    ```
    """
    
    result1 = parse_yaml_with_schema(
        response1,
        required_fields=["questions"],
        field_types={"questions": list}
    )
    print(f"Test 1 - Valid schema parse: {result1}")
    assert result1 is not None
    assert isinstance(result1["questions"], list)
    assert len(result1["questions"]) == 3
    
    # Test 2: Invalid schema
    response2 = """
    ```yaml
    questions: "not a list"
    ```
    """
    
    result2 = parse_yaml_with_schema(
        response2,
        required_fields=["questions"],
        field_types={"questions": list}
    )
    print(f"Test 2 - Invalid schema: {result2}")
    assert result2 is None
    
    logger.info("✅ Parse with schema tests passed")


def test_malformed_responses():
    """Test various malformed responses that LLMs might generate"""
    logger.info("=== Test Malformed Responses ===")
    
    # Test 1: Mixed content
    response1 = """
    I think the classification is:
    
    ```yaml
    type: medical_question
    confidence: high
    ```
    
    Hope this helps!
    """
    
    result1 = parse_yaml_response(response1)
    print(f"Test 1 - Mixed content: {result1}")
    assert result1 is not None
    assert result1["type"] == "medical_question"
    
    # Test 2: Multiple code blocks
    response2 = """
    First attempt:
    ```yaml
    wrong: data
    ```
    
    Actually, the correct one is:
    ```yaml
    type: greeting
    confidence: medium
    ```
    """
    
    result2 = parse_yaml_response(response2)
    print(f"Test 2 - Multiple code blocks: {result2}")
    # Should get the first parseable one
    
    # Test 3: Partial YAML
    response3 = """
    type: medical_question
    confidence: high
    but this part is not valid YAML syntax [
    """
    
    result3 = parse_yaml_response(response3)
    print(f"Test 3 - Partial YAML: {result3}")
    
    logger.info("✅ Malformed response tests passed")


def main():
    """Run all tests"""
    logger.info("🧪 Starting Response Parser Tests")
    
    try:
        test_basic_yaml_parsing()
        test_schema_validation()
        test_edge_cases()
        test_parse_with_schema()
        test_malformed_responses()
        
        logger.info("🎉 All tests passed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
