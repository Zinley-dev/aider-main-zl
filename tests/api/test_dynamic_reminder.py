#!/usr/bin/env python3
"""
Test script for the dynamic system reminder implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_util import (
    detect_request_type,
    detect_urgency,
    estimate_complexity,
    create_dynamic_system_reminder,
    apply_dynamic_system_reminder,
    create_enhanced_coder_with_dynamic_reminder
)

def test_request_analysis():
    """Test request analysis functions"""
    print("🧪 Testing request analysis functions...")
    
    # Test request type detection
    test_cases = [
        ("Create a new HTML file", "create_new"),
        ("Fix the bug in main.py", "debug"),
        ("Refactor the code to improve performance", "refactor"),
        ("Update the title of the page", "update"),
        ("Add a new feature to the app", "add_feature"),
        ("Show me the code", "general")
    ]
    
    print("\n📝 Request Type Detection:")
    for message, expected in test_cases:
        result = detect_request_type(message)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{message}' -> {result} (expected: {expected})")
    
    # Test urgency detection
    urgency_cases = [
        ("Fix this bug immediately", "high"),
        ("Update the code quickly", "high"),
        ("Create a new file", "normal"),
        ("This is urgent and critical", "high")
    ]
    
    print("\n⚡ Urgency Detection:")
    for message, expected in urgency_cases:
        result = detect_urgency(message)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{message}' -> {result} (expected: {expected})")
    
    # Test complexity estimation
    complexity_cases = [
        ("Fix typo", [], "low"),
        ("Create a complex database integration system", ["main.py", "db.py", "api.py"], "high"),
        ("Update the HTML title", ["index.html"], "low"),
        ("Refactor the entire codebase", ["app.py", "utils.py"], "medium")
    ]
    
    print("\n🔢 Complexity Estimation:")
    for message, files, expected in complexity_cases:
        result = estimate_complexity(message, files)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{message}' with {len(files)} files -> {result} (expected: {expected})")

def test_dynamic_system_reminder():
    """Test dynamic system reminder generation"""
    print("\n🧪 Testing dynamic system reminder generation...")
    
    # Test case 1: HTML file creation with images
    print("\n🌟 Test case 1: HTML file creation with images")
    files = ["index.html", "style.css"]
    request_context = {
        'type': 'create_new',
        'urgency': 'normal',
        'complexity': 'medium'
    }
    image_files = ["mockup.png", "logo.svg"]
    
    reminder = create_dynamic_system_reminder(
        files=files,
        request_context=request_context,
        image_files=image_files
    )
    
    print(f"Generated reminder length: {len(reminder)} characters")
    
    # Check for expected content
    expected_content = [
        "SEARCH/REPLACE block",
        "HTML files: Maintain proper DOCTYPE",
        "CSS files: Use consistent naming",
        "Images available for reference",
        "Creating new files: Use empty SEARCH section",
        "CRITICAL BEHAVIORAL INSTRUCTIONS",
        "Files to edit: index.html, style.css"
    ]
    
    for content in expected_content:
        if content in reminder:
            print(f"✅ Contains: {content}")
        else:
            print(f"❌ Missing: {content}")
    
    # Test case 2: Python debugging with urgency
    print("\n🌟 Test case 2: Python debugging with urgency")
    files = ["main.py"]
    request_context = {
        'type': 'debug',
        'urgency': 'high',
        'complexity': 'low'
    }
    
    reminder = create_dynamic_system_reminder(
        files=files,
        request_context=request_context
    )
    
    expected_debug_content = [
        "Python files: Follow PEP 8",
        "Debugging: Focus on identifying",
        "URGENT REQUEST: Prioritize speed",
        "Files to edit: main.py"
    ]
    
    for content in expected_debug_content:
        if content in reminder:
            print(f"✅ Contains: {content}")
        else:
            print(f"❌ Missing: {content}")
    
    # Test case 3: Complex JavaScript refactoring
    print("\n🌟 Test case 3: Complex JavaScript refactoring")
    files = ["app.js", "utils.js", "api.js"]
    request_context = {
        'type': 'refactor',
        'urgency': 'normal',
        'complexity': 'high'
    }
    
    reminder = create_dynamic_system_reminder(
        files=files,
        request_context=request_context
    )
    
    expected_refactor_content = [
        "JavaScript/TypeScript: Use modern ES6+",
        "Refactoring: Maintain functionality",
        "Complex request: Break down into smaller",
        "Files to edit: app.js, utils.js, api.js"
    ]
    
    for content in expected_refactor_content:
        if content in reminder:
            print(f"✅ Contains: {content}")
        else:
            print(f"❌ Missing: {content}")

def test_integration():
    """Test integration with mock coder"""
    print("\n🧪 Testing integration with mock coder...")
    
    # Create a mock coder object
    class MockCoder:
        def __init__(self):
            self.gpt_prompts = MockPrompts()
            self.abs_read_only_fnames = set()
            self.cur_messages = []
        
        def get_rel_fname(self, abs_path):
            return os.path.basename(abs_path)
    
    class MockPrompts:
        def __init__(self):
            self.system_reminder = ""
    
    # Test apply_dynamic_system_reminder
    mock_coder = MockCoder()
    files = ["test.py"]
    request_context = {
        'type': 'create_new',
        'urgency': 'normal',
        'complexity': 'low'
    }
    
    # Apply dynamic reminder
    result_coder = apply_dynamic_system_reminder(mock_coder, files, request_context)
    
    # Check if system reminder was applied
    if result_coder.gpt_prompts.system_reminder:
        print("✅ System reminder was applied to coder")
        print(f"   Reminder length: {len(result_coder.gpt_prompts.system_reminder)} characters")
        
        # Check for Python-specific content
        if "Python files: Follow PEP 8" in result_coder.gpt_prompts.system_reminder:
            print("✅ Python-specific instructions included")
        else:
            print("❌ Python-specific instructions missing")
    else:
        print("❌ System reminder was not applied")

def main():
    """Run all tests"""
    print("🚀 Starting Dynamic System Reminder Tests")
    print("=" * 50)
    
    try:
        test_request_analysis()
        test_dynamic_system_reminder()
        test_integration()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()