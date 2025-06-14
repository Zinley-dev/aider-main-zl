#!/usr/bin/env python3
"""
Test script để demo Aider REST API với streaming (SSE)
"""

import requests
import json
import time
import os

# Cấu hình
API_BASE_URL = "http://localhost:8000"
TEST_REPO_PATH = "/Users/hoangnm/Desktop/test"
TEST_FILE = "index.html"

def test_streaming_chat():
    """Test streaming chat với SSE"""
    print("🚀 Testing Streaming Chat API...")
    
    # Tạo session trước
    session_data = {
        "repo_path": TEST_REPO_PATH,
        "files": [TEST_FILE],
        "model": "snowx/gpt-4o",
        "edit_format": "whole"
    }
    
    print(f"📁 Creating session for repo: {TEST_REPO_PATH}")
    print(f"📋 Session data: {session_data}")
    
    try:
        session_response = requests.post(f"{API_BASE_URL}/sessions", json=session_data)
        print(f"📡 Session response status: {session_response.status_code}")
        
        if session_response.status_code != 200:
            print(f"❌ Failed to create session: {session_response.text}")
            return
    except Exception as e:
        print(f"❌ Session request failed: {e}")
        return
    
    session_info = session_response.json()
    session_id = session_info["session_id"]
    print(f"✅ Session created: {session_id}")
    
    # Streaming chat request
    chat_data = {
        "message": "Change the title to 'My Professional Resume' and add a header with name 'John Doe' and title 'Software Engineer'",
        "session_id": session_id,
        "stream": True  # Enable streaming
    }
    
    print("🔄 Starting streaming chat...")
    print("=" * 60)
    
    # Gửi streaming request
    response = requests.post(
        f"{API_BASE_URL}/chat",
        json=chat_data,
        stream=True,  # Enable streaming
        headers={
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Chat request failed: {response.text}")
        return
    
    # Xử lý streaming response
    final_result = None
    event_type = None
    
    try:
        for line in response.iter_lines(decode_unicode=True):
            if line:
                # Parse SSE format
                if line.startswith("event: "):
                    event_type = line[7:]  # Remove "event: "
                elif line.startswith("data: "):
                    data_str = line[6:]  # Remove "data: "
                    try:
                        data = json.loads(data_str)
                        
                        # Hiển thị event dựa trên type
                        if event_type == "start":
                            print(f"🟢 {data.get('message', '')}")
                        elif event_type == "info":
                            print(f"ℹ️  {data.get('message', '')}")
                        elif event_type == "processing":
                            print(f"⚙️  {data.get('message', '')}")
                        elif event_type == "tool_output":
                            print(f"🔧 Tool: {data.get('message', '')}")
                        elif event_type == "tool_error":
                            print(f"❌ Tool Error: {data.get('message', '')}")
                        elif event_type == "tool_warning":
                            print(f"⚠️  Tool Warning: {data.get('message', '')}")
                        elif event_type == "ai_output":
                            print(f"🤖 AI: {data.get('message', '')}")
                        elif event_type == "assistant_output":
                            print(f"👨‍💻 Assistant: {data.get('message', '')}")
                        elif event_type == "file_write":
                            filename = data.get('filename', '')
                            content_length = data.get('content_length', 0)
                            success = data.get('success', False)
                            status = "✅" if success else "❌"
                            print(f"{status} File Write: {filename} ({content_length} chars)")
                        elif event_type == "response":
                            print(f"💬 Response: {data.get('message', '')[:100]}...")
                        elif event_type == "complete":
                            print(f"🎉 Complete!")
                            final_result = data
                            # Hiển thị kết quả cuối
                            print(f"   - Tokens sent: {data.get('tokens_sent', 0)}")
                            print(f"   - Tokens received: {data.get('tokens_received', 0)}")
                            print(f"   - Cost: ${data.get('cost', 0.0):.4f}")
                            print(f"   - Edited files: {len(data.get('edited_files', []))}")
                        elif event_type == "heartbeat":
                            print("💓 Heartbeat")
                        elif event_type == "error":
                            print(f"💥 Error: {data.get('message', '')}")
                        else:
                            print(f"📝 {event_type}: {data}")
                            
                    except json.JSONDecodeError:
                        print(f"⚠️  Invalid JSON: {data_str}")
                        
    except KeyboardInterrupt:
        print("\n⏹️  Streaming interrupted by user")
    except Exception as e:
        print(f"💥 Streaming error: {e}")
    
    print("=" * 60)
    
    # Kiểm tra file đã được tạo/sửa chưa
    test_file_path = os.path.join(TEST_REPO_PATH, TEST_FILE)
    if os.path.exists(test_file_path):
        with open(test_file_path, 'r') as f:
            content = f.read()
        print(f"📄 File content ({len(content)} chars):")
        print(content[:200] + "..." if len(content) > 200 else content)
    else:
        print(f"❌ File not found: {test_file_path}")
    
    return final_result

def test_non_streaming_chat():
    """Test non-streaming chat để so sánh"""
    print("\n🚀 Testing Non-Streaming Chat API...")
    
    # Tạo session trước
    session_data = {
        "repo_path": TEST_REPO_PATH,
        "files": [TEST_FILE],
        "model": "snowx/gpt-4o",
        "edit_format": "whole"  # Sử dụng format hợp lệ
    }
    
    print(f"📋 Session data: {session_data}")
    
    try:
        session_response = requests.post(f"{API_BASE_URL}/sessions", json=session_data)
        print(f"📡 Session response status: {session_response.status_code}")
        
        if session_response.status_code != 200:
            print(f"❌ Failed to create session: {session_response.text}")
            return
    except Exception as e:
        print(f"❌ Session request failed: {e}")
        return
    
    session_info = session_response.json()
    session_id = session_info["session_id"]
    print(f"✅ Session created: {session_id}")
    
    # Non-streaming chat request
    chat_data = {
        "message": "Change the title to 'Updated Resume' and add a contact section with email 'john@example.com'",
        "session_id": session_id,
        "stream": False  # Disable streaming
    }
    
    print("⏳ Sending non-streaming request...")
    start_time = time.time()
    
    response = requests.post(f"{API_BASE_URL}/chat", json=chat_data)
    
    end_time = time.time()
    print(f"⏱️  Request completed in {end_time - start_time:.2f} seconds")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Response received:")
        print(f"   - Tokens sent: {result.get('tokens_sent', 0)}")
        print(f"   - Tokens received: {result.get('tokens_received', 0)}")
        print(f"   - Cost: ${result.get('cost', 0.0):.4f}")
        print(f"   - Edited files: {len(result.get('edited_files', []))}")
    else:
        print(f"❌ Request failed: {response.text}")

def main():
    """Main test function"""
    print("🧪 Aider REST API Streaming Test")
    print("=" * 60)
    
    # Kiểm tra server
    try:
        health_response = requests.get(f"{API_BASE_URL}/health")
        if health_response.status_code != 200:
            print(f"❌ Server not available: {API_BASE_URL}")
            return
        print(f"✅ Server is running: {API_BASE_URL}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server: {API_BASE_URL}")
        return
    
    # Kiểm tra models có sẵn
    try:
        models_response = requests.get(f"{API_BASE_URL}/models")
        if models_response.status_code == 200:
            models = models_response.json()
            print(f"📋 Available models: {models.get('models', [])[:5]}...")  # Show first 5
        else:
            print(f"⚠️ Could not fetch models: {models_response.status_code}")
    except Exception as e:
        print(f"⚠️ Error fetching models: {e}")
    
    # Kiểm tra test directory
    if not os.path.exists(TEST_REPO_PATH):
        print(f"❌ Test directory not found: {TEST_REPO_PATH}")
        return
    print(f"✅ Test directory exists: {TEST_REPO_PATH}")
    
    # Test streaming
    streaming_result = test_streaming_chat()
    
    # Test non-streaming để so sánh
    # test_non_streaming_chat()
    
    print("\n🎯 Test completed!")

if __name__ == "__main__":
    main() 