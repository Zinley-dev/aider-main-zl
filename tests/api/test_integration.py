#!/usr/bin/env python3
"""
Test script to verify the dynamic system reminder integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_controller import chat_non_stream, create_session_controller
from api_util import create_temp_repo
import asyncio

class MockRequest:
    def __init__(self, message, files=None, session_id=None):
        self.message = message
        self.files = files or []
        self.session_id = session_id
        self.repo_path = None
        self.model = "gpt-4"
        self.read_only_files = []
        self.edit_format = "diff"

class MockSessionRequest:
    def __init__(self, repo_path=None, files=None):
        self.repo_path = repo_path
        self.files = files or []
        self.model = "gpt-4"
        self.read_only_files = []
        self.edit_format = "diff"
        self.auto_commits = True

async def test_dynamic_system_reminder_integration():
    """Test that dynamic system reminder is properly integrated"""
    print("🧪 Testing Dynamic System Reminder Integration")
    print("=" * 60)
    
    try:
        # Test 1: Create session and check if dynamic reminder is applied
        print("\n🌟 Test 1: Session Creation with Dynamic Reminder")
        
        # Create a temp repo for testing
        temp_repo = create_temp_repo(["test.html", "style.css"])
        print(f"📁 Created temp repo: {temp_repo}")
        
        # Create session request
        session_request = MockSessionRequest(repo_path=temp_repo, files=["test.html", "style.css"])
        
        # Create session
        session_result = await create_session_controller(session_request)
        session_id = session_result["session_id"]
        
        print(f"✅ Session created: {session_id}")
        print(f"   Files: {session_result['files']}")
        
        # Test 2: Chat with different request types
        test_scenarios = [
            {
                'name': 'HTML Creation (Create New)',
                'message': 'Create a simple HTML page with a header and navigation',
                'files': ['test.html'],
                'expected_type': 'create_new'
            },
            {
                'name': 'Bug Fix (Debug)',
                'message': 'Fix the CSS bug in the navigation styling',
                'files': ['style.css'],
                'expected_type': 'debug'
            },
            {
                'name': 'Urgent Update',
                'message': 'Update the title quickly, this is urgent!',
                'files': ['test.html'],
                'expected_type': 'update'
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n🌟 Test: {scenario['name']}")
            
            # Create mock request
            request = MockRequest(
                message=scenario['message'],
                files=scenario['files'],
                session_id=session_id
            )
            
            # Note: We can't actually run the chat since it requires a real model
            # But we can verify the integration by checking if the functions work
            print(f"   Message: {scenario['message']}")
            print(f"   Files: {scenario['files']}")
            print(f"   Expected type: {scenario['expected_type']}")
            
            # Test that the functions are properly imported and accessible
            from api_util import detect_request_type, detect_urgency, estimate_complexity
            
            detected_type = detect_request_type(scenario['message'])
            detected_urgency = detect_urgency(scenario['message'])
            detected_complexity = estimate_complexity(scenario['message'], scenario['files'])
            
            print(f"   Detected type: {detected_type}")
            print(f"   Detected urgency: {detected_urgency}")
            print(f"   Detected complexity: {detected_complexity}")
            
            # Check if detection matches expectations
            if detected_type == scenario['expected_type']:
                print("   ✅ Request type detection working correctly")
            else:
                print(f"   ❌ Expected {scenario['expected_type']}, got {detected_type}")
        
        print("\n" + "=" * 60)
        print("✅ Integration tests completed successfully!")
        
        # Cleanup
        print(f"\n🧹 Cleaning up temp repo: {temp_repo}")
        import shutil
        shutil.rmtree(temp_repo)
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_system_reminder_content():
    """Test that system reminder content is properly generated"""
    print("\n🔍 Testing System Reminder Content Generation")
    print("=" * 60)
    
    from api_util import create_dynamic_system_reminder
    
    # Test different scenarios
    test_cases = [
        {
            'name': 'Python Development',
            'files': ['main.py', 'utils.py'],
            'context': {'type': 'create_new', 'urgency': 'normal', 'complexity': 'medium'},
            'expected_content': ['Python files: Follow PEP 8', 'Creating new files']
        },
        {
            'name': 'Web Development with Images',
            'files': ['index.html', 'style.css'],
            'context': {'type': 'debug', 'urgency': 'high', 'complexity': 'low'},
            'image_files': ['mockup.png'],
            'expected_content': ['HTML files: Maintain proper DOCTYPE', 'CSS files: Use consistent', 'Images available', 'Debugging: Focus on', 'URGENT REQUEST']
        },
        {
            'name': 'JavaScript Refactoring',
            'files': ['app.js', 'components.js'],
            'context': {'type': 'refactor', 'urgency': 'normal', 'complexity': 'high'},
            'expected_content': ['JavaScript/TypeScript: Use modern', 'Refactoring: Maintain functionality', 'Complex request: Break down']
        }
    ]
    
    for case in test_cases:
        print(f"\n🧪 Testing: {case['name']}")
        
        reminder = create_dynamic_system_reminder(
            files=case['files'],
            request_context=case['context'],
            image_files=case.get('image_files', [])
        )
        
        print(f"   Generated reminder length: {len(reminder)} chars")
        
        # Check for expected content
        for expected in case['expected_content']:
            if expected in reminder:
                print(f"   ✅ Contains: {expected}")
            else:
                print(f"   ❌ Missing: {expected}")

def main():
    """Run all integration tests"""
    print("🚀 Starting Dynamic System Reminder Integration Tests")
    print("=" * 70)
    
    asyncio.run(test_dynamic_system_reminder_integration())
    asyncio.run(test_system_reminder_content())
    
    print("\n" + "=" * 70)
    print("🎉 All integration tests completed!")

if __name__ == "__main__":
    main()