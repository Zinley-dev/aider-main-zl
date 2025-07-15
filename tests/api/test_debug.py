#!/usr/bin/env python3

import requests
import json
import os
import time

# Test configuration
API_BASE = "http://localhost:8000"
TEST_DIR = "/Users/hoangnm/Desktop/test"
TEST_FILE = "debug.html"

def test_streaming_debug():
    print("🧪 Debug Streaming Test")
    print("=" * 50)
    
    # Ensure test directory exists
    os.makedirs(TEST_DIR, exist_ok=True)
    
    # Create a fresh test file
    test_file_path = os.path.join(TEST_DIR, TEST_FILE)
    original_content = """<!DOCTYPE html>
<html>
<head>
    <title>Debug Test</title>
</head>
<body>
    <h1>Original Debug Content</h1>
</body>
</html>"""
    
    with open(test_file_path, 'w') as f:
        f.write(original_content)
    
    print(f"📄 Created fresh test file: {test_file_path}")
    print(f"📝 Original content length: {len(original_content)} chars")
    
    # Create a new session
    session_data = {
        "repo_path": TEST_DIR,
        "files": [TEST_FILE],
        "model": "snowx/gpt-4o",
        "edit_format": "whole"
    }
    
    print(f"📁 Creating new session...")
    session_response = requests.post(f"{API_BASE}/sessions", json=session_data)
    
    if session_response.status_code != 200:
        print(f"❌ Failed to create session: {session_response.text}")
        return
    
    session_info = session_response.json()
    session_id = session_info["session_id"]
    print(f"✅ Session created: {session_id}")
    
    # Test streaming chat
    chat_data = {
        "message": "Change the title to 'Debug Success' and the h1 to 'Modified Debug Content'",
        "session_id": session_id,
        "stream": True
    }
    
    print(f"🚀 Sending streaming request...")
    
    try:
        response = requests.post(f"{API_BASE}/chat", json=chat_data, stream=True, timeout=30)
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("📡 Streaming events:")
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith("event: "):
                        event_type = line[7:]
                        print(f"   🔸 {event_type}")
                    elif line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if 'message' in data:
                                msg = data['message']
                                if event_type == "response":
                                    print(f"      📝 Response: {msg[:100]}...")
                                elif event_type == "complete":
                                    print(f"      📊 Edited files: {len(data.get('edited_files', []))}")
                                else:
                                    print(f"      📝 {msg}")
                        except:
                            pass
        
        # Check if file was actually modified
        with open(test_file_path, 'r') as f:
            new_content = f.read()
        
        print(f"\n📄 File after API call:")
        print(f"   - Original length: {len(original_content)} chars")
        print(f"   - New length: {len(new_content)} chars")
        print(f"   - Content changed: {new_content != original_content}")
        
        if new_content != original_content:
            print("✅ SUCCESS: File was actually modified!")
            print("📝 New content:")
            print(new_content)
        else:
            print("❌ FAILED: File was not modified")
            print("📝 Current content:")
            print(new_content)
            
    except Exception as e:
        print(f"💥 Request failed: {e}")

if __name__ == "__main__":
    test_streaming_debug() 