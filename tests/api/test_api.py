#!/usr/bin/env python3
"""
Script test để kiểm tra Aider REST API
"""

import requests
import json
import time
import os

# Cấu hình API
API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_list_models():
    """Test list models endpoint"""
    print("\n🔍 Testing list models...")
    try:
        response = requests.get(f"{API_BASE_URL}/models")
        if response.status_code == 200:
            models = response.json()
            print("✅ Models endpoint working")
            print(f"   Available OpenAI models: {len(models.get('openai', []))}")
            print(f"   Available Anthropic models: {len(models.get('anthropic', []))}")
            print(f"   Model aliases: {len(models.get('aliases', {}))}")
            return True
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Models endpoint error: {e}")
        return False

def test_create_session():
    """Test create session endpoint"""
    print("\n🔍 Testing create session...")
    try:
        response = requests.post(f"{API_BASE_URL}/sessions")
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data.get("session_id")
            print("✅ Session created successfully")
            print(f"   Session ID: {session_id}")
            return session_id
        else:
            print(f"❌ Session creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Session creation error: {e}")
        return None

def test_simple_chat(session_id):
    """Test simple chat without files"""
    print("\n🔍 Testing simple chat...")
    try:
        chat_request = {
            "message": "Hello! Can you explain what you are and what you can do?",
            "session_id": session_id,
            "model": "gpt-4o"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=chat_request,
            timeout=60
        )
        
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ Simple chat successful")
            print(f"   Response length: {len(chat_response.get('response', ''))}")
            print(f"   Tokens sent: {chat_response.get('tokens_sent', 0)}")
            print(f"   Tokens received: {chat_response.get('tokens_received', 0)}")
            print(f"   Cost: ${chat_response.get('cost', 0):.4f}")
            
            # Print first 200 characters of response
            response_text = chat_response.get('response', '')
            if response_text:
                print(f"   Response preview: {response_text[:200]}...")
            
            return True
        else:
            print(f"❌ Simple chat failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Simple chat error: {e}")
        return False

def test_chat_with_file(session_id):
    """Test chat with a file"""
    print("\n🔍 Testing chat with file...")
    
    # Tạo file test
    test_file = "test_example.py"
    test_content = '''def hello_world():
    """A simple hello world function"""
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
'''
    
    try:
        # Tạo file test
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        chat_request = {
            "message": "Please add a function to calculate the factorial of a number to this Python file.",
            "session_id": session_id,
            "files": [test_file],
            "model": "gpt-4o"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=chat_request,
            timeout=120
        )
        
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ File chat successful")
            print(f"   Files edited: {len(chat_response.get('edited_files', []))}")
            
            edited_files = chat_response.get('edited_files', [])
            if edited_files:
                print(f"   Edited file: {edited_files[0].get('name', 'Unknown')}")
                print(f"   New content length: {len(edited_files[0].get('content', ''))}")
            
            return True
        else:
            print(f"❌ File chat failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ File chat error: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)

def test_session_management(session_id):
    """Test session management endpoints"""
    print("\n🔍 Testing session management...")
    
    try:
        # Test get files in session
        response = requests.get(f"{API_BASE_URL}/sessions/{session_id}/files")
        if response.status_code == 200:
            files_data = response.json()
            print(f"✅ Session files retrieved: {files_data.get('files', [])}")
        else:
            print(f"⚠️  Session files failed: {response.status_code}")
        
        # Test delete session
        response = requests.delete(f"{API_BASE_URL}/sessions/{session_id}")
        if response.status_code == 200:
            print("✅ Session deleted successfully")
            return True
        else:
            print(f"❌ Session deletion failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Session management error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Aider REST API Tests")
    print("=" * 50)
    
    # Check if API keys are set
    api_keys_status = []
    if os.getenv("OPENAI_API_KEY"):
        api_keys_status.append("OpenAI ✅")
    else:
        api_keys_status.append("OpenAI ❌")
    
    if os.getenv("ANTHROPIC_API_KEY"):
        api_keys_status.append("Anthropic ✅")
    else:
        api_keys_status.append("Anthropic ❌")
    
    print(f"API Keys: {', '.join(api_keys_status)}")
    print()
    
    # Run tests
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Health check
    total_tests += 1
    if test_health_check():
        tests_passed += 1
    
    # Test 2: List models
    total_tests += 1
    if test_list_models():
        tests_passed += 1
    
    # Test 3: Create session
    total_tests += 1
    session_id = test_create_session()
    if session_id:
        tests_passed += 1
        
        # Test 4: Simple chat (only if we have a session and API key)
        if os.getenv("OPENAI_API_KEY"):
            total_tests += 1
            if test_simple_chat(session_id):
                tests_passed += 1
            
            # Test 5: Chat with file
            total_tests += 1
            if test_chat_with_file(session_id):
                tests_passed += 1
        else:
            print("\n⚠️  Skipping chat tests - no OPENAI_API_KEY found")
        
        # Test 6: Session management
        total_tests += 1
        if test_session_management(session_id):
            tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"🏁 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 