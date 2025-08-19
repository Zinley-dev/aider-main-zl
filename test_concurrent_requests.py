#!/usr/bin/env python3
"""
Test script to verify concurrent streaming requests don't mix data
"""

import asyncio
import aiohttp
import json
import time
from typing import List, Dict

API_URL = "http://localhost:8080"  # Update this to match your API URL

async def stream_request(session: aiohttp.ClientSession, request_id: str, session_id: str, message: str) -> Dict:
    """
    Make a streaming request and collect all events
    """
    print(f"[{request_id}] Starting request: {message}")
    
    payload = {
        "message": message,
        "session_id": session_id,
        "files": ["test.html"],
        "stream": True,
        "model": "claude-3-5-sonnet-20241022"
    }
    
    events = []
    start_time = time.time()
    
    try:
        async with session.post(f"{API_URL}/chat", json=payload) as response:
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('event:'):
                    event_type = line.split(':', 1)[1].strip()
                elif line.startswith('data:'):
                    data = line.split(':', 1)[1].strip()
                    try:
                        data_json = json.loads(data)
                        events.append({
                            'type': event_type,
                            'data': data_json,
                            'request_id': request_id,
                            'timestamp': time.time() - start_time
                        })
                        
                        # Check if this event has a request_id in the data
                        if 'request_id' in data_json:
                            print(f"[{request_id}] Event has request_id: {data_json['request_id']}")
                            
                    except json.JSONDecodeError:
                        print(f"[{request_id}] Failed to parse JSON: {data}")
                        
    except Exception as e:
        print(f"[{request_id}] Error: {e}")
        
    print(f"[{request_id}] Completed. Received {len(events)} events in {time.time() - start_time:.2f}s")
    return {
        'request_id': request_id,
        'events': events,
        'event_count': len(events)
    }

async def test_concurrent_streaming():
    """
    Test 3 concurrent streaming requests to the same session
    """
    print("Starting concurrent streaming test...")
    
    # Create a session first
    async with aiohttp.ClientSession() as session:
        # Create initial session
        create_response = await session.post(f"{API_URL}/sessions", json={
            "files": ["test.html"],
            "model": "claude-3-5-sonnet-20241022"
        })
        session_data = await create_response.json()
        session_id = session_data['session_id']
        print(f"Created session: {session_id}")
        
        # Make 3 concurrent requests to the same session
        tasks = [
            stream_request(session, "REQ1", session_id, "Change the title to 'Request 1'"),
            stream_request(session, "REQ2", session_id, "Add a paragraph saying 'This is request 2'"),
            stream_request(session, "REQ3", session_id, "Change the background color to blue")
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Analyze results
        print("\n=== RESULTS ANALYSIS ===")
        for result in results:
            req_id = result['request_id']
            events = result['events']
            
            # Check if any events are from other requests
            mixed_events = []
            for event in events:
                # Check various ways events might be mixed
                event_data = event['data']
                event_str = str(event_data)
                
                # Check if event contains content from other requests
                if req_id == "REQ1" and ("request 2" in event_str.lower() or "blue" in event_str.lower()):
                    mixed_events.append(event)
                elif req_id == "REQ2" and ("request 1" in event_str.lower() or "blue" in event_str.lower()):
                    mixed_events.append(event)
                elif req_id == "REQ3" and ("request 1" in event_str.lower() or "request 2" in event_str.lower()):
                    mixed_events.append(event)
            
            print(f"\n[{req_id}] Total events: {result['event_count']}")
            if mixed_events:
                print(f"[{req_id}] ⚠️  FOUND {len(mixed_events)} MIXED EVENTS!")
                for mixed in mixed_events[:3]:  # Show first 3
                    print(f"  - Type: {mixed['type']}, Data: {str(mixed['data'])[:100]}...")
            else:
                print(f"[{req_id}] ✅ No mixed events detected")
            
            # Show sample events
            print(f"[{req_id}] Sample events:")
            for event in events[:5]:
                print(f"  - {event['type']}: {str(event['data'])[:80]}...")

if __name__ == "__main__":
    asyncio.run(test_concurrent_streaming())