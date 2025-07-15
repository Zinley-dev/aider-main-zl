#!/usr/bin/env python3
"""
Usage examples for the Dynamic System Reminder implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_util import (
    create_enhanced_coder_with_dynamic_reminder,
    apply_dynamic_system_reminder,
    create_dynamic_system_reminder,
    get_session_context,
    update_session_context
)

def example_api_integration():
    """
    Example showing how to integrate with an API server
    """
    print("🔗 API Integration Example")
    print("=" * 50)
    
    # Simulate API request data
    class MockRequest:
        def __init__(self):
            self.message = "Create a responsive HTML page with navigation"
            self.files = ["index.html", "style.css"]
            self.session_id = "test_session_123"
            self.repo_path = "/tmp/test_project"
            self.model = "gpt-4"
    
    request = MockRequest()
    
    # Method 1: Use the enhanced coder creation function
    print("\n🌟 Method 1: Enhanced coder creation")
    try:
        session, session_id = create_enhanced_coder_with_dynamic_reminder(
            session_id=request.session_id,
            repo_path=request.repo_path,
            model=request.model,
            files=request.files,
            request_message=request.message,
            session_context={'user_preferences': {'style': 'modern'}}
        )
        
        print(f"✅ Created session: {session_id}")
        print(f"   Coder type: {type(session['coder'])}")
        print(f"   System reminder length: {len(session['coder'].gpt_prompts.system_reminder)} chars")
        
    except Exception as e:
        print(f"❌ Error creating enhanced coder: {e}")
    
    # Method 2: Apply dynamic reminder to existing coder
    print("\n🌟 Method 2: Apply to existing coder")
    # This would be used if you already have a coder instance
    # apply_dynamic_system_reminder(existing_coder, request.files, request_context)

def example_different_scenarios():
    """
    Examples of different request scenarios
    """
    print("\n🎯 Different Scenario Examples")
    print("=" * 50)
    
    scenarios = [
        {
            'name': 'Bug Fix (Urgent)',
            'message': 'Fix the critical bug in authentication immediately',
            'files': ['auth.py', 'models.py'],
            'expected_context': {'type': 'debug', 'urgency': 'high', 'complexity': 'medium'}
        },
        {
            'name': 'New Feature Development',
            'message': 'Add a new feature for user dashboard with charts',
            'files': ['dashboard.html', 'charts.js', 'dashboard.css'],
            'expected_context': {'type': 'add_feature', 'urgency': 'normal', 'complexity': 'high'}
        },
        {
            'name': 'Simple Update',
            'message': 'Update the page title',
            'files': ['index.html'],
            'expected_context': {'type': 'update', 'urgency': 'normal', 'complexity': 'low'}
        },
        {
            'name': 'Code Refactoring',
            'message': 'Refactor the entire codebase to improve performance',
            'files': ['main.py', 'utils.py', 'api.py', 'models.py'],
            'expected_context': {'type': 'refactor', 'urgency': 'normal', 'complexity': 'high'}
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print(f"   Message: {scenario['message']}")
        print(f"   Files: {scenario['files']}")
        
        # Create dynamic reminder for this scenario
        from api_util import detect_request_type, detect_urgency, estimate_complexity
        
        actual_context = {
            'type': detect_request_type(scenario['message']),
            'urgency': detect_urgency(scenario['message']),
            'complexity': estimate_complexity(scenario['message'], scenario['files'])
        }
        
        print(f"   Context: {actual_context}")
        
        # Generate reminder
        reminder = create_dynamic_system_reminder(
            files=scenario['files'],
            request_context=actual_context,
            image_files=['mockup.png'] if 'dashboard' in scenario['message'] else []
        )
        
        print(f"   Reminder length: {len(reminder)} chars")
        
        # Check if it contains expected content
        if actual_context['type'] == 'debug':
            if 'Debugging: Focus on identifying' in reminder:
                print("   ✅ Contains debug-specific instructions")
        elif actual_context['type'] == 'add_feature':
            if 'Adding features: Integrate new functionality' in reminder:
                print("   ✅ Contains feature-specific instructions")
        elif actual_context['urgency'] == 'high':
            if 'URGENT REQUEST' in reminder:
                print("   ✅ Contains urgency instructions")

def example_file_type_specific():
    """
    Examples showing file type specific instructions
    """
    print("\n📁 File Type Specific Examples")
    print("=" * 50)
    
    file_scenarios = [
        {
            'name': 'Python Development',
            'files': ['main.py', 'utils.py'],
            'expected_content': 'Python files: Follow PEP 8'
        },
        {
            'name': 'Web Development',
            'files': ['index.html', 'style.css', 'app.js'],
            'expected_content': ['HTML files: Maintain proper DOCTYPE', 'CSS files: Use consistent', 'JavaScript/TypeScript: Use modern']
        },
        {
            'name': 'Configuration',
            'files': ['config.json', 'settings.json'],
            'expected_content': 'JSON files: Maintain proper JSON syntax'
        },
        {
            'name': 'Mixed Development',
            'files': ['backend.py', 'frontend.html', 'styles.css', 'config.json'],
            'expected_content': ['Python files', 'HTML files', 'CSS files', 'JSON files']
        }
    ]
    
    for scenario in file_scenarios:
        print(f"\n🔧 {scenario['name']}")
        print(f"   Files: {scenario['files']}")
        
        reminder = create_dynamic_system_reminder(
            files=scenario['files'],
            request_context={'type': 'create_new', 'urgency': 'normal', 'complexity': 'medium'}
        )
        
        expected = scenario['expected_content']
        if isinstance(expected, str):
            expected = [expected]
        
        for content in expected:
            if content in reminder:
                print(f"   ✅ Contains: {content}")
            else:
                print(f"   ❌ Missing: {content}")

def example_with_images():
    """
    Example with image files for UI development
    """
    print("\n🖼️ Image Context Example")
    print("=" * 50)
    
    reminder = create_dynamic_system_reminder(
        files=['index.html', 'style.css'],
        request_context={'type': 'create_new', 'urgency': 'normal', 'complexity': 'medium'},
        image_files=['mockup.png', 'logo.svg', 'hero-image.jpg']
    )
    
    print(f"Reminder length: {len(reminder)} chars")
    
    image_related_content = [
        'Images available for reference: mockup.png, logo.svg, hero-image.jpg',
        'Use these images as visual reference when building UI components'
    ]
    
    for content in image_related_content:
        if content in reminder:
            print(f"✅ Contains: {content}")
        else:
            print(f"❌ Missing: {content}")

def main():
    """
    Run all usage examples
    """
    print("🚀 Dynamic System Reminder Usage Examples")
    print("=" * 60)
    
    try:
        example_api_integration()
        example_different_scenarios()
        example_file_type_specific()
        example_with_images()
        
        print("\n" + "=" * 60)
        print("✅ All usage examples completed successfully!")
        
        print("\n📖 Integration Guide:")
        print("1. Import the functions from api_util.py")
        print("2. Use create_enhanced_coder_with_dynamic_reminder() for new coders")
        print("3. Use apply_dynamic_system_reminder() for existing coders")
        print("4. The dynamic reminder will be automatically applied based on:")
        print("   - Request message analysis")
        print("   - File types being edited")
        print("   - Image files available")
        print("   - Session context")
        
    except Exception as e:
        print(f"\n❌ Usage example failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()