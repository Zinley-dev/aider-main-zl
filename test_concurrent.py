#!/usr/bin/env python3
"""
Test script to verify concurrent API requests don't block each other
"""

import asyncio
import aiohttp
import time
import json
from concurrent.futures import ThreadPoolExecutor

API_BASE = "http://localhost:8000"

async def test_health_check():
    """Test health check endpoint"""
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        async with session.get(f"{API_BASE}/health") as response:
            end_time = time.time()
            data = await response.json()
            return {
                "endpoint": "/health",
                "status": response.status,
                "response_time": end_time - start_time,
                "data": data
            }

async def test_create_session():
    """Test create session endpoint"""
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        payload = {
            "model": "gpt-4",
            "files": [],
            "edit_format": "whole"
        }
        async with session.post(f"{API_BASE}/sessions", json=payload) as response:
            end_time = time.time()
            data = await response.json()
            return {
                "endpoint": "/sessions",
                "status": response.status,
                "response_time": end_time - start_time,
                "data": data
            }

async def test_chat_request():
    """Test chat endpoint with simple request"""
    async with aiohttp.ClientSession() as session:
        # First create a session
        session_payload = {
            "model": "gpt-4",
            "files": [],
            "edit_format": "whole"
        }
        async with session.post(f"{API_BASE}/sessions", json=session_payload) as response:
            session_data = await response.json()
            session_id = session_data["session_id"]
        
        # Then send chat request
        start_time = time.time()
        chat_payload = {
            "message": "Create a simple HTML file with title 'Test Page'",
            "session_id": session_id,
            "files": ["index.html"],
            "stream": False
        }
        async with session.post(f"{API_BASE}/chat", json=chat_payload) as response:
            end_time = time.time()
            data = await response.json() if response.status == 200 else {"error": await response.text()}
            return {
                "endpoint": "/chat",
                "status": response.status,
                "response_time": end_time - start_time,
                "session_id": session_id,
                "data": data
            }

async def test_concurrent_requests():
    """Test that multiple requests can run concurrently"""
    print("🚀 Starting concurrent API tests...")
    
    # Test 1: Health checks should be fast and not block each other
    print("\n=== Test 1: Concurrent Health Checks ===")
    tasks = [test_health_check() for _ in range(5)]
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time
    
    print(f"Total time for 5 health checks: {total_time:.2f}s")
    for i, result in enumerate(results):
        print(f"  Health check {i+1}: {result['response_time']:.3f}s - Status: {result['status']}")
    
    # Test 2: Session creation should be concurrent
    print("\n=== Test 2: Concurrent Session Creation ===")
    tasks = [test_create_session() for _ in range(3)]
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time
    
    print(f"Total time for 3 session creations: {total_time:.2f}s")
    for i, result in enumerate(results):
        print(f"  Session {i+1}: {result['response_time']:.3f}s - Status: {result['status']}")
        if result['status'] == 200:
            print(f"    Session ID: {result['data'].get('session_id', 'N/A')}")
    
    # Test 3: Mix health checks with session creation
    print("\n=== Test 3: Mixed Concurrent Requests ===")
    tasks = []
    tasks.extend([test_health_check() for _ in range(3)])
    tasks.extend([test_create_session() for _ in range(2)])
    
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time
    
    print(f"Total time for 5 mixed requests: {total_time:.2f}s")
    for i, result in enumerate(results):
        print(f"  Request {i+1} ({result['endpoint']}): {result['response_time']:.3f}s - Status: {result['status']}")

async def test_health_during_chat():
    """Test that health checks work while chat is processing"""
    print("\n=== Test 4: Health Check During Chat Processing ===")
    
    # Start a chat request (this might take longer)
    chat_task = asyncio.create_task(test_chat_request())
    
    # Wait a bit for chat to start, then send health checks
    await asyncio.sleep(1)
    
    health_tasks = [test_health_check() for _ in range(3)]
    start_time = time.time()
    health_results = await asyncio.gather(*health_tasks)
    health_time = time.time() - start_time
    
    print(f"Health checks completed in {health_time:.2f}s while chat was processing")
    for i, result in enumerate(health_results):
        print(f"  Health check {i+1}: {result['response_time']:.3f}s - Status: {result['status']}")
    
    # Wait for chat to complete
    chat_result = await chat_task
    print(f"Chat request completed: {chat_result['response_time']:.2f}s - Status: {chat_result['status']}")

if __name__ == "__main__":
    print("🧪 Testing API concurrency improvements...")
    print("Make sure the API server is running on http://localhost:8000")
    
    try:
        asyncio.run(test_concurrent_requests())
        asyncio.run(test_health_during_chat())
        print("\n✅ All tests completed!")
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}") 