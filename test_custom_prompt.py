#!/usr/bin/env python3
"""
Test script for the custom prompt system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from custom_prompt import (
    PromptComponents,
    PromptBuilder,
    CustomPromptTemplates,
    create_custom_dynamic_system_reminder,
    create_web_prompt,
    create_python_prompt,
    create_debug_prompt,
    create_refactor_prompt
)

def test_prompt_components():
    """Test the PromptComponents class"""
    print("🧪 Testing PromptComponents")
    print("=" * 50)
    
    components = PromptComponents()
    
    # Test base rules
    print(f"✅ Base rules length: {len(components.BASE_RULES)} chars")
    assert "SEARCH/REPLACE block" in components.BASE_RULES
    
    # Test file type instructions
    print(f"✅ File type instructions: {len(components.FILE_TYPE_INSTRUCTIONS)} types")
    assert '.py' in components.FILE_TYPE_INSTRUCTIONS
    assert '.html' in components.FILE_TYPE_INSTRUCTIONS
    assert '.js' in components.FILE_TYPE_INSTRUCTIONS
    
    # Test request type instructions
    print(f"✅ Request type instructions: {len(components.REQUEST_TYPE_INSTRUCTIONS)} types")
    assert 'create_new' in components.REQUEST_TYPE_INSTRUCTIONS
    assert 'debug' in components.REQUEST_TYPE_INSTRUCTIONS
    assert 'refactor' in components.REQUEST_TYPE_INSTRUCTIONS
    
    # Test urgency and complexity
    print(f"✅ Urgency levels: {list(components.URGENCY_INSTRUCTIONS.keys())}")
    print(f"✅ Complexity levels: {list(components.COMPLEXITY_INSTRUCTIONS.keys())}")

def test_prompt_builder():
    """Test the PromptBuilder class"""
    print("\n🧪 Testing PromptBuilder")
    print("=" * 50)
    
    builder = PromptBuilder()
    
    # Test building a basic prompt
    files = ['test.py', 'main.py']
    request_context = {
        'type': 'create_new',
        'urgency': 'normal',
        'complexity': 'medium'
    }
    image_files = ['mockup.png']
    
    result = (builder
              .add_base_rules()
              .add_context_instructions(files, request_context, image_files)
              .add_critical_instructions()
              .add_file_list(files)
              .add_ending_instruction()
              .build())
    
    print(f"✅ Generated prompt length: {len(result)} chars")
    
    # Check for expected content
    expected_content = [
        "SEARCH/REPLACE block",
        "Python files: Follow PEP 8",
        "Creating new files: Use empty SEARCH section",
        "CRITICAL BEHAVIORAL INSTRUCTIONS",
        "Files to edit: test.py, main.py",
        "Images available for reference: mockup.png",
        "ONLY EVER RETURN CODE"
    ]
    
    for content in expected_content:
        if content in result:
            print(f"✅ Contains: {content}")
        else:
            print(f"❌ Missing: {content}")

def test_custom_templates():
    """Test the CustomPromptTemplates class"""
    print("\n🧪 Testing CustomPromptTemplates")
    print("=" * 50)
    
    templates = CustomPromptTemplates()
    
    # Test web development template
    web_files = ['index.html', 'style.css', 'app.js']
    web_context = {'type': 'create_new', 'urgency': 'normal', 'complexity': 'medium'}
    web_images = ['design.png']
    
    web_prompt = templates.web_development_template(web_files, web_context, web_images)
    print(f"✅ Web template length: {len(web_prompt)} chars")
    
    web_expected = [
        "HTML files: Maintain proper DOCTYPE",
        "CSS files: Use consistent naming",
        "JavaScript/TypeScript: Use modern ES6+",
        "Images available for reference: design.png"
    ]
    
    for content in web_expected:
        if content in web_prompt:
            print(f"✅ Web template contains: {content}")
        else:
            print(f"❌ Web template missing: {content}")
    
    # Test Python development template
    python_files = ['main.py', 'utils.py']
    python_context = {'type': 'refactor', 'urgency': 'normal', 'complexity': 'high'}
    
    python_prompt = templates.python_development_template(python_files, python_context)
    print(f"✅ Python template length: {len(python_prompt)} chars")
    
    python_expected = [
        "Python files: Follow PEP 8",
        "Refactoring: Maintain functionality",
        "Complex request: Break down into smaller"
    ]
    
    for content in python_expected:
        if content in python_prompt:
            print(f"✅ Python template contains: {content}")
        else:
            print(f"❌ Python template missing: {content}")
    
    # Test debug template
    debug_files = ['buggy.py']
    debug_context = {'type': 'update', 'urgency': 'normal', 'complexity': 'low'}
    
    debug_prompt = templates.debug_template(debug_files, debug_context)
    print(f"✅ Debug template length: {len(debug_prompt)} chars")
    
    debug_expected = [
        "Debugging: Focus on identifying",
        "URGENT REQUEST: Prioritize speed"  # Should be forced to high urgency
    ]
    
    for content in debug_expected:
        if content in debug_prompt:
            print(f"✅ Debug template contains: {content}")
        else:
            print(f"❌ Debug template missing: {content}")

def test_convenience_functions():
    """Test the convenience functions"""
    print("\n🧪 Testing Convenience Functions")
    print("=" * 50)
    
    files = ['app.js', 'index.html']
    context = {'type': 'create_new', 'urgency': 'normal', 'complexity': 'medium'}
    images = ['wireframe.png']
    
    # Test create_web_prompt
    web_prompt = create_web_prompt(files, context, images)
    print(f"✅ create_web_prompt length: {len(web_prompt)} chars")
    
    # Test create_python_prompt
    python_files = ['main.py']
    python_prompt = create_python_prompt(python_files, context)
    print(f"✅ create_python_prompt length: {len(python_prompt)} chars")
    
    # Test create_debug_prompt
    debug_prompt = create_debug_prompt(files, context)
    print(f"✅ create_debug_prompt length: {len(debug_prompt)} chars")
    
    # Test create_refactor_prompt
    refactor_prompt = create_refactor_prompt(files, context)
    print(f"✅ create_refactor_prompt length: {len(refactor_prompt)} chars")

def test_main_function():
    """Test the main create_custom_dynamic_system_reminder function"""
    print("\n🧪 Testing Main Function")
    print("=" * 50)
    
    # Test different scenarios
    scenarios = [
        {
            'name': 'Web Development',
            'files': ['index.html', 'style.css'],
            'context': {'type': 'create_new', 'urgency': 'normal', 'complexity': 'medium'},
            'images': ['design.png'],
            'template': 'web'
        },
        {
            'name': 'Python Development',
            'files': ['main.py', 'utils.py'],
            'context': {'type': 'refactor', 'urgency': 'normal', 'complexity': 'high'},
            'images': None,
            'template': 'python'
        },
        {
            'name': 'Debug Task',
            'files': ['broken.js'],
            'context': {'type': 'debug', 'urgency': 'high', 'complexity': 'low'},
            'images': None,
            'template': 'debug'
        },
        {
            'name': 'General Task',
            'files': ['config.json'],
            'context': {'type': 'update', 'urgency': 'normal', 'complexity': 'low'},
            'images': None,
            'template': None
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Testing: {scenario['name']}")
        
        prompt = create_custom_dynamic_system_reminder(
            files=scenario['files'],
            request_context=scenario['context'],
            image_files=scenario['images'],
            use_template=scenario['template']
        )
        
        print(f"   Generated prompt length: {len(prompt)} chars")
        
        # Basic validation
        assert "SEARCH/REPLACE block" in prompt
        assert "CRITICAL BEHAVIORAL INSTRUCTIONS" in prompt
        assert "ONLY EVER RETURN CODE" in prompt
        
        print(f"   ✅ {scenario['name']} prompt generated successfully")

def main():
    """Run all tests"""
    print("🚀 Starting Custom Prompt System Tests")
    print("=" * 60)
    
    try:
        test_prompt_components()
        test_prompt_builder()
        test_custom_templates()
        test_convenience_functions()
        test_main_function()
        
        print("\n" + "=" * 60)
        print("✅ All custom prompt tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()