#!/usr/bin/env python3
"""
Test script để kiểm tra refactor đã hoạt động
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test import các module mới"""
    try:
        from utils.prompts import (
            PROMPT_CLASSIFY_INPUT,
            PROMPT_COMPOSE_ANSWER,
            PROMPT_SUGGEST_FOLLOWUPS
        )
        print("✅ Import prompts thành công")
        
        from utils.helpers import (
            get_persona_for,
            get_topics_by_role,
            build_kb_context,
            classify_input_pattern
        )
        print("✅ Import helpers thành công")
        
        from nodes import (
            ClassifyInput,
            ComposeAnswer,
            TopicSuggestResponse,
            MainAgentNode
        )
        print("✅ Import nodes thành công")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_helpers():
    """Test các helper functions"""
    try:
        from utils.helpers import get_persona_for, classify_input_pattern
        
        # Test get_persona_for
        persona = get_persona_for("bác sĩ nha khoa")
        assert "audience" in persona
        assert "tone" in persona
        print("✅ get_persona_for hoạt động")
        
        # Test classify_input_pattern
        result = classify_input_pattern("chào bạn")
        assert result["type"] == "greeting"
        assert result["confidence"] == "high"
        print("✅ classify_input_pattern hoạt động")
        
        return True
        
    except Exception as e:
        print(f"❌ Helpers test failed: {e}")
        return False

def test_prompts():
    """Test các prompts"""
    try:
        from utils.prompts import PROMPT_CLASSIFY_INPUT
        
        # Test prompt formatting
        formatted = PROMPT_CLASSIFY_INPUT.format(
            query="test query",
            role="test role"
        )
        assert "test query" in formatted
        assert "test role" in formatted
        print("✅ Prompts formatting hoạt động")
        
        return True
        
    except Exception as e:
        print(f"❌ Prompts test failed: {e}")
        return False

def test_nodes():
    """Test các nodes đã refactor"""
    try:
        from nodes import ClassifyInput
        
        # Test node creation
        node = ClassifyInput()
        assert hasattr(node, 'prep')
        assert hasattr(node, 'exec')
        assert hasattr(node, 'post')
        print("✅ Node structure đúng")
        
        return True
        
    except Exception as e:
        print(f"❌ Nodes test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing refactor...")
    
    tests = [
        test_imports,
        test_helpers,
        test_prompts,
        test_nodes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Tất cả tests passed! Refactor thành công!")
        return True
    else:
        print("❌ Một số tests failed. Cần kiểm tra lại.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
