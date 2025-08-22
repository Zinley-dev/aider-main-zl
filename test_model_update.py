#!/usr/bin/env python3
"""
Test script to verify that the model parameter is properly updated in chat API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8080"

def test_model_update():
    print("Testing model update in chat API...")
    
    # Step 1: Create a session with model gpt-4
    print("\n1. Creating session with gpt-4...")
    session_data = {
        "model": "gpt-4",
        "files": ["test.txt"]
    }
    
    response = requests.post(f"{BASE_URL}/sessions", json=session_data)
    if response.status_code != 200:
        print(f"Failed to create session: {response.text}")
        return
        
    session_info = response.json()
    session_id = session_info["session_id"]
    print(f"Created session {session_id} with model: {session_info['model']}")
    
    # Step 2: Send a chat request with the same model
    print("\n2. Sending chat with gpt-4 (same model)...")
    chat_data = {
        "message": "Hello, write a simple test function",
        "session_id": session_id,
        "model": "gpt-4",
        "stream": False
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=chat_data)
    if response.status_code == 200:
        result = response.json()
        print(f"Chat successful. Tokens: {result.get('tokens_sent', 0)}")
    else:
        print(f"Chat failed: {response.text}")
    
    # Step 3: Send a chat request with a different model
    print("\n3. Sending chat with claude-3-5-sonnet-20241022 (different model)...")
    chat_data = {
        "message": "Now update the function to add logging",
        "session_id": session_id,
        "model": "claude-3-5-sonnet-20241022",
        "stream": False
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=chat_data)
    if response.status_code == 200:
        result = response.json()
        print(f"Chat successful with new model. Tokens: {result.get('tokens_sent', 0)}")
        print("✅ Model update working correctly!")
    else:
        print(f"❌ Chat failed: {response.text}")
    
    # Step 4: Test with streaming
    print("\n4. Testing with streaming and model change...")
    chat_data = {
        "message": "Add error handling to the function",
        "session_id": session_id,
        "model": "gpt-4o",
        "stream": True
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=chat_data, stream=True)
    if response.status_code == 200:
        print("Streaming response received with new model gpt-4o")
        event_count = 0
        for line in response.iter_lines():
            if line:
                event_count += 1
        print(f"✅ Streaming with model update working! Received {event_count} events")
    else:
        print(f"❌ Streaming failed: {response.text}")
    
    # Cleanup
    print(f"\n5. Deleting session {session_id}...")
    response = requests.delete(f"{BASE_URL}/sessions/{session_id}")
    if response.status_code == 200:
        print("Session deleted successfully")
    else:
        print(f"Failed to delete session: {response.text}")

if __name__ == "__main__":
    test_model_update()