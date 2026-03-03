"""
Debug script để tìm lỗi trong response parser
"""

import yaml
import re
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_extract_from_code_fences(response: str):
    """Debug version of _extract_from_code_fences - improved"""
    print(f"Input response: {repr(response)}")
    
    # Improved YAML code fence patterns
    yaml_patterns = [
        r'```yaml\s*\n(.*?)\n\s*```',
        r'```YAML\s*\n(.*?)\n\s*```', 
        r'```yml\s*\n(.*?)\n\s*```',
        r'```YML\s*\n(.*?)\n\s*```',
        r'```\s*\n(.*?)\n\s*```',  # Generic code fence
        # Alternative patterns for edge cases
        r'```yaml(.*?)```',
        r'```YAML(.*?)```',
        r'```yml(.*?)```',
        r'```(.*?)```',  # Most generic
    ]
    
    for i, pattern in enumerate(yaml_patterns):
        print(f"Testing pattern {i}: {pattern}")
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            print(f"Found match with pattern {i}: {repr(content)}")
            if content and len(content) > 0:
                # Additional cleanup - normalize indentation
                lines = content.split('\n')
                print(f"Original lines: {lines}")
                
                # Remove empty lines at start and end
                while lines and not lines[0].strip():
                    lines.pop(0)
                while lines and not lines[-1].strip():
                    lines.pop()
                
                if lines:
                    # Find minimum indentation (excluding empty lines)
                    non_empty_lines = [line for line in lines if line.strip()]
                    if non_empty_lines:
                        min_indent = min(len(line) - len(line.lstrip()) for line in non_empty_lines)
                        print(f"Min indentation found: {min_indent}")
                        # Remove common indentation from all lines
                        cleaned_lines = []
                        for line in lines:
                            if line.strip():  # Non-empty line
                                if len(line) >= min_indent:
                                    cleaned_lines.append(line[min_indent:])
                                else:
                                    cleaned_lines.append(line.lstrip())  # Remove all leading whitespace if less than min
                            else:  # Empty line
                                cleaned_lines.append('')
                        cleaned_content = '\n'.join(cleaned_lines).strip()
                        print(f"Cleaned content: {repr(cleaned_content)}")
                    else:
                        cleaned_content = content.strip()
                else:
                    cleaned_content = content.strip()
                
                return cleaned_content
        else:
            print(f"No match with pattern {i}")
    
    return None

def debug_yaml_parsing():
    """Debug the exact test case that's failing"""
    response1 = """
    Here is the classification:
    ```yaml
    type: medical_question
    confidence: high
    reason: Contains medical terms
    ```
    """
    
    print("=== Debug YAML Parsing ===")
    print(f"Original response: {repr(response1)}")
    
    # Step 1: Try to extract from code fence
    extracted = debug_extract_from_code_fences(response1)
    print(f"Extracted content: {repr(extracted)}")
    
    if extracted:
        # Step 2: Try to parse as YAML
        try:
            result = yaml.safe_load(extracted)
            print(f"YAML parsed result: {result}")
            print(f"Result type: {type(result)}")
            if isinstance(result, dict):
                print("✅ Successfully parsed as dict")
            else:
                print("❌ Not a dict")
        except Exception as e:
            print(f"❌ YAML parsing failed: {e}")
    else:
        print("❌ No content extracted from code fence")
    
    # Let's also try the full response
    print("\n=== Try full response parsing ===")
    try:
        full_result = yaml.safe_load(response1)
        print(f"Full response parsed: {full_result}")
    except Exception as e:
        print(f"Full response parsing failed: {e}")

if __name__ == "__main__":
    debug_yaml_parsing()
