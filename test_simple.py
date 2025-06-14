#!/usr/bin/env python3

import requests
import json
import os
import time

# Test configuration
API_BASE = "http://localhost:8000"
TEST_DIR = "/Users/hoangnm/Desktop/test"
TEST_FILE = "index.html"

def test_simple_edit():
    print("🧪 Simple API Test - Force File Edit")
    print("=" * 50)
    
    # Ensure test directory exists
    os.makedirs(TEST_DIR, exist_ok=True)
    
    # Create a simple test file
    test_file_path = os.path.join(TEST_DIR, TEST_FILE)
    original_content = """<!DOCTYPE html>
<html>
<head>
    <title>Original Title</title>
</head>
<body>
    <h1>Original Content</h1>
</body>
</html>"""
    
    with open(test_file_path, 'w') as f:
        f.write(original_content)
    
    print(f"📄 Created test file: {test_file_path}")
    print(f"📝 Original content length: {len(original_content)} chars")
    
    # Test non-streaming first
    print("\n🔄 Testing NON-STREAMING mode...")
    test_mode(False, test_file_path, original_content)
    
    # Reset file
    with open(test_file_path, 'w') as f:
        f.write(original_content)
    
    # Test streaming
    print("\n🔄 Testing STREAMING mode...")
    test_mode(True, test_file_path, original_content)

def test_mode(stream_mode, test_file_path, original_content):
    payload = {
        "message": "Change the title to 'Updated Title' and the h1 content to 'Updated Content'",
        "repo_path": TEST_DIR,
        "files": [TEST_FILE],
        "model": "snowx/gpt-4o",
        "stream": stream_mode
    }
    
    print(f"🚀 Sending {'STREAMING' if stream_mode else 'NON-STREAMING'} request...")
    
    try:
        if stream_mode:
            # Handle streaming response
            response = requests.post(f"{API_BASE}/chat", json=payload, timeout=30, stream=True)
            print(f"📡 Response status: {response.status_code}")
            
            if response.status_code == 200:
                print("📡 Streaming events:")
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('event: '):
                            event_type = line_str[7:]
                            print(f"   🔸 {event_type}")
                        elif line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])
                                if 'message' in data:
                                    msg = data['message'][:100] + "..." if len(data['message']) > 100 else data['message']
                                    print(f"      📝 {msg}")
                            except:
                                pass
        else:
            # Handle regular response
            response = requests.post(f"{API_BASE}/chat", json=payload, timeout=30)
            print(f"📡 Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API Response:")
                print(f"   - Response length: {len(data.get('response', ''))} chars")
                print(f"   - Edited files: {len(data.get('edited_files', []))}")
        
        # Check if file was actually modified
        with open(test_file_path, 'r') as f:
            new_content = f.read()
        
        print(f"📄 File after API call:")
        print(f"   - New content length: {len(new_content)} chars")
        print(f"   - Content changed: {new_content != original_content}")
        
        if new_content != original_content:
            print("✅ SUCCESS: File was actually modified!")
        else:
            print("❌ FAILED: File was not modified")
            
    except Exception as e:
        print(f"💥 Request failed: {e}")

if __name__ == "__main__":
    test_simple_edit() 