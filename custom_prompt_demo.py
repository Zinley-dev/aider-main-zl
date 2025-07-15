#!/usr/bin/env python3
"""
Demonstration of the custom prompt system features
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from custom_prompt import (
    PromptBuilder,
    CustomPromptTemplates,
    create_custom_dynamic_system_reminder,
    create_web_prompt,
    create_python_prompt,
    create_debug_prompt,
    create_refactor_prompt
)

def demo_basic_builder():
    """Demonstrate basic PromptBuilder usage"""
    print("🔧 Basic PromptBuilder Demo")
    print("=" * 60)
    
    builder = PromptBuilder()
    
    # Build a custom prompt step by step
    files = ['frontend.js', 'backend.py', 'styles.css']
    request_context = {
        'type': 'add_feature',
        'urgency': 'high',
        'complexity': 'high'
    }
    image_files = ['wireframe.png', 'mockup.jpg']
    
    prompt = (builder
              .add_base_rules()
              .add_context_instructions(files, request_context, image_files)
              .add_critical_instructions()
              .add_file_list(files)
              .add_ending_instruction()
              .build())
    
    print(f"Generated prompt length: {len(prompt)} characters")
    print("\nPrompt preview (first 300 chars):")
    print("-" * 40)
    print(prompt[:300] + "...")
    print("-" * 40)
    
    # Show key sections
    print("\n📋 Key sections included:")
    sections = [
        ("Base SEARCH/REPLACE rules", "SEARCH/REPLACE block"),
        ("JavaScript instructions", "JavaScript/TypeScript: Use modern ES6+"),
        ("Python instructions", "Python files: Follow PEP 8"),
        ("CSS instructions", "CSS files: Use consistent naming"),
        ("Feature addition guidance", "Adding features: Integrate new functionality"),
        ("Urgency instructions", "URGENT REQUEST: Prioritize speed"),
        ("Complexity instructions", "Complex request: Break down into smaller"),
        ("Image references", "Images available for reference: wireframe.png, mockup.jpg"),
        ("Critical instructions", "CRITICAL BEHAVIORAL INSTRUCTIONS"),
        ("File list", "Files to edit: frontend.js, backend.py, styles.css"),
        ("Ending instruction", "ONLY EVER RETURN CODE")
    ]
    
    for section_name, search_text in sections:
        if search_text in prompt:
            print(f"   ✅ {section_name}")
        else:
            print(f"   ❌ {section_name}")

def demo_specialized_templates():
    """Demonstrate specialized templates"""
    print("\n🎨 Specialized Templates Demo")
    print("=" * 60)
    
    templates = CustomPromptTemplates()
    
    # Web development template
    print("\n🌐 Web Development Template:")
    web_files = ['index.html', 'app.js', 'style.css']
    web_context = {'type': 'create_new', 'urgency': 'normal', 'complexity': 'medium'}
    web_images = ['design.png', 'logo.svg']
    
    web_prompt = templates.web_development_template(web_files, web_context, web_images)
    print(f"   Length: {len(web_prompt)} chars")
    print(f"   Contains HTML guidance: {'HTML files: Maintain proper DOCTYPE' in web_prompt}")
    print(f"   Contains CSS guidance: {'CSS files: Use consistent naming' in web_prompt}")
    print(f"   Contains JS guidance: {'JavaScript/TypeScript: Use modern ES6+' in web_prompt}")
    print(f"   Contains image references: {'Images available for reference' in web_prompt}")
    
    # Python development template
    print("\n🐍 Python Development Template:")
    python_files = ['main.py', 'utils.py', 'config.py']
    python_context = {'type': 'refactor', 'urgency': 'normal', 'complexity': 'high'}
    
    python_prompt = templates.python_development_template(python_files, python_context)
    print(f"   Length: {len(python_prompt)} chars")
    print(f"   Contains PEP 8 guidance: {'Python files: Follow PEP 8' in python_prompt}")
    print(f"   Contains refactor guidance: {'Refactoring: Maintain functionality' in python_prompt}")
    print(f"   Contains complexity guidance: {'Complex request: Break down' in python_prompt}")
    
    # Debug template
    print("\n🐛 Debug Template:")
    debug_files = ['broken.js', 'error.log']
    debug_context = {'type': 'update', 'urgency': 'normal', 'complexity': 'low'}
    
    debug_prompt = templates.debug_template(debug_files, debug_context)
    print(f"   Length: {len(debug_prompt)} chars")
    print(f"   Contains debug guidance: {'Debugging: Focus on identifying' in debug_prompt}")
    print(f"   Contains urgency override: {'URGENT REQUEST' in debug_prompt}")
    print(f"   Forces high urgency: {'high' in str(debug_context)}")

def demo_convenience_functions():
    """Demonstrate convenience functions"""
    print("\n🚀 Convenience Functions Demo")
    print("=" * 60)
    
    # Test different scenarios
    scenarios = [
        {
            'name': 'Quick Web Prompt',
            'func': create_web_prompt,
            'files': ['landing.html', 'main.css'],
            'context': {'type': 'create_new', 'urgency': 'normal', 'complexity': 'low'},
            'images': ['hero.jpg']
        },
        {
            'name': 'Quick Python Prompt',
            'func': create_python_prompt,
            'files': ['analyzer.py', 'tests.py'],
            'context': {'type': 'add_feature', 'urgency': 'normal', 'complexity': 'medium'},
            'images': None
        },
        {
            'name': 'Quick Debug Prompt',
            'func': create_debug_prompt,
            'files': ['buggy_script.py'],
            'context': {'type': 'general', 'urgency': 'low', 'complexity': 'low'},
            'images': None
        },
        {
            'name': 'Quick Refactor Prompt',
            'func': create_refactor_prompt,
            'files': ['legacy.js', 'old_utils.js'],
            'context': {'type': 'general', 'urgency': 'normal', 'complexity': 'high'},
            'images': None
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📝 {scenario['name']}:")
        if scenario['images']:
            prompt = scenario['func'](scenario['files'], scenario['context'], scenario['images'])
        else:
            prompt = scenario['func'](scenario['files'], scenario['context'])
        
        print(f"   Length: {len(prompt)} chars")
        print(f"   Files: {scenario['files']}")
        print(f"   Context: {scenario['context']}")
        if scenario['images']:
            print(f"   Images: {scenario['images']}")

def demo_template_selection():
    """Demonstrate automatic template selection"""
    print("\n🎯 Automatic Template Selection Demo")
    print("=" * 60)
    
    # Test different file combinations to see template selection
    test_cases = [
        {
            'name': 'Web Development Files',
            'files': ['index.html', 'app.js', 'style.css'],
            'context': {'type': 'create_new', 'urgency': 'normal', 'complexity': 'medium'},
            'images': ['mockup.png'],
            'expected_template': 'web'
        },
        {
            'name': 'Python Only Files',
            'files': ['main.py', 'utils.py'],
            'context': {'type': 'refactor', 'urgency': 'normal', 'complexity': 'high'},
            'images': None,
            'expected_template': 'python'
        },
        {
            'name': 'Debug Request',
            'files': ['any.js'],
            'context': {'type': 'debug', 'urgency': 'high', 'complexity': 'low'},
            'images': None,
            'expected_template': 'debug'
        },
        {
            'name': 'Refactor Request',
            'files': ['legacy.py'],
            'context': {'type': 'refactor', 'urgency': 'normal', 'complexity': 'medium'},
            'images': None,
            'expected_template': 'refactor'
        },
        {
            'name': 'Mixed Files (General)',
            'files': ['config.json', 'readme.md'],
            'context': {'type': 'update', 'urgency': 'normal', 'complexity': 'low'},
            'images': None,
            'expected_template': 'general'
        }
    ]
    
    for case in test_cases:
        print(f"\n📋 {case['name']}:")
        print(f"   Files: {case['files']}")
        print(f"   Context: {case['context']}")
        print(f"   Expected template: {case['expected_template']}")
        
        # Test with different template specifications
        prompt_default = create_custom_dynamic_system_reminder(
            files=case['files'],
            request_context=case['context'],
            image_files=case['images']
        )
        
        prompt_explicit = create_custom_dynamic_system_reminder(
            files=case['files'],
            request_context=case['context'],
            image_files=case['images'],
            use_template=case['expected_template'] if case['expected_template'] != 'general' else None
        )
        
        print(f"   Default prompt length: {len(prompt_default)} chars")
        print(f"   Explicit template prompt length: {len(prompt_explicit)} chars")
        
        # Check for template-specific content
        if case['expected_template'] == 'web' and case['images']:
            has_images = 'Images available for reference' in prompt_default
            print(f"   ✅ Contains image references: {has_images}")
        elif case['expected_template'] == 'python':
            has_pep8 = 'Python files: Follow PEP 8' in prompt_default
            print(f"   ✅ Contains PEP 8 guidance: {has_pep8}")
        elif case['expected_template'] == 'debug':
            has_debug = 'Debugging: Focus on identifying' in prompt_default
            print(f"   ✅ Contains debug guidance: {has_debug}")

def main():
    """Run all demonstrations"""
    print("🎨 Custom Prompt System Demonstration")
    print("=" * 70)
    
    demo_basic_builder()
    demo_specialized_templates()
    demo_convenience_functions()
    demo_template_selection()
    
    print("\n" + "=" * 70)
    print("🎉 Custom Prompt System Demo Complete!")
    print("\nKey Benefits:")
    print("✅ Modular and extensible prompt components")
    print("✅ Specialized templates for different development scenarios")
    print("✅ Automatic template selection based on file types and context")
    print("✅ Easy to use convenience functions")
    print("✅ Comprehensive file type support")
    print("✅ Context-aware instructions")
    print("✅ Clean separation of concerns")

if __name__ == "__main__":
    main()