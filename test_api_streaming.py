#!/usr/bin/env python3
"""
Tests for streaming API functionality
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)

class TestStreamingChat:
    """Test streaming chat functionality"""
    
    @patch('api_server.get_or_create_session')
    def test_streaming_endpoint_response_format(self, mock_get_session):
        """Test that streaming endpoint returns proper SSE format"""
        # Mock session
        mock_coder = MagicMock()
        mock_io = MagicMock()
        mock_session = {
            "coder": mock_coder,
            "io": mock_io,
            "repo_path": "/tmp/test"
        }
        mock_get_session.return_value = (mock_session, "test-session-id")
        
        chat_data = {
            "message": "Test streaming message",
            "stream": True
        }
        
        response = client.post("/chat", json=chat_data)
        
        # Should return streaming response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == "no-cache"
    
    def test_non_streaming_chat(self):
        """Test non-streaming chat returns JSON"""
        with patch('api_server.get_or_create_session') as mock_get_session, \
             patch('api_server._run_coder_blocking') as mock_run_coder:
            
            # Mock session
            mock_coder = MagicMock()
            mock_io = MagicMock()
            mock_io.get_captured_output.return_value = ""
            mock_io.get_captured_errors.return_value = ""
            mock_io.get_captured_warnings.return_value = ""
            
            mock_session = {
                "coder": mock_coder,
                "io": mock_io,
                "repo_path": "/tmp/test"
            }
            
            mock_get_session.return_value = (mock_session, "test-session-id")
            mock_run_coder.return_value = "Test response"
            
            # Mock coder attributes
            mock_coder.aider_edited_files = set()
            mock_coder.message_tokens_sent = 100
            mock_coder.message_tokens_received = 50
            mock_coder.message_cost = 0.001
            
            chat_data = {
                "message": "Test non-streaming message",
                "stream": False
            }
            
            response = client.post("/chat", json=chat_data)
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
            
            data = response.json()
            assert "response" in data
            assert "session_id" in data


class TestSSEFormat:
    """Test Server-Sent Events format compliance"""
    
    def test_sse_event_format(self):
        """Test that SSE events are properly formatted"""
        from api_server import create_sse_response
        
        async def mock_events():
            yield {"type": "start", "data": {"message": "Starting..."}}
            yield {"type": "message", "data": {"content": "Hello"}}
            yield {"type": "end", "data": {"message": "Done"}}
        
        # This is a generator function, we need to test it properly
        import asyncio
        
        async def test_sse_format():
            events = mock_events()
            sse_generator = create_sse_response(events)
            
            results = []
            async for sse_data in sse_generator:
                results.append(sse_data)
            
            # Check format
            assert len(results) == 3
            
            # First event
            assert "event: start\n" in results[0]
            assert "data: " in results[0]
            assert '{"message": "Starting..."}' in results[0]
            assert results[0].endswith("\n\n")
            
            # Second event  
            assert "event: message\n" in results[1]
            assert "data: " in results[1]
            assert '{"content": "Hello"}' in results[1]
            
            # Third event
            assert "event: end\n" in results[2]
            assert "data: " in results[2]
            assert '{"message": "Done"}' in results[2]
        
        # Run the async test
        asyncio.run(test_sse_format())


class TestConcurrentRequests:
    """Test handling of concurrent requests"""
    
    @patch('api_server.get_or_create_session')
    @patch('api_server._run_coder_blocking')
    def test_multiple_sessions_concurrent(self, mock_run_coder, mock_get_session):
        """Test that multiple sessions can be handled concurrently"""
        import threading
        import time
        
        # Mock different sessions
        def mock_session_side_effect(*args, **kwargs):
            session_id = f"session-{threading.current_thread().ident}"
            mock_coder = MagicMock()
            mock_io = MagicMock()
            mock_io.get_captured_output.return_value = ""
            mock_io.get_captured_errors.return_value = ""
            mock_io.get_captured_warnings.return_value = ""
            
            mock_session = {
                "coder": mock_coder,
                "io": mock_io,
                "repo_path": f"/tmp/test-{session_id}"
            }
            
            mock_coder.aider_edited_files = set()
            mock_coder.message_tokens_sent = 100
            mock_coder.message_tokens_received = 50
            mock_coder.message_cost = 0.001
            
            return (mock_session, session_id)
        
        mock_get_session.side_effect = mock_session_side_effect
        mock_run_coder.return_value = "Response"
        
        results = []
        
        def make_request(session_data):
            try:
                response = client.post("/chat", json={
                    "message": f"Test message for {session_data}",
                    "stream": False
                })
                results.append({
                    "status": response.status_code,
                    "session_data": session_data,
                    "response_data": response.json() if response.status_code == 200 else None
                })
            except Exception as e:
                results.append({
                    "status": "error",
                    "session_data": session_data,
                    "error": str(e)
                })
        
        # Create multiple threads to test concurrent requests
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_request, args=(f"session-{i}",))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)
        
        # Check results
        assert len(results) == 3
        for result in results:
            assert result["status"] == 200
            assert result["response_data"] is not None
            assert "session_id" in result["response_data"]


class TestErrorHandlingInStreaming:
    """Test error handling in streaming scenarios"""
    
    @patch('api_server.get_or_create_session')
    def test_streaming_with_session_error(self, mock_get_session):
        """Test streaming behavior when session creation fails"""
        mock_get_session.side_effect = Exception("Session creation failed")
        
        chat_data = {
            "message": "Test message",
            "stream": True
        }
        
        response = client.post("/chat", json=chat_data)
        
        # Should handle error gracefully
        assert response.status_code == 500
    
    @patch('api_server.get_or_create_session')
    def test_non_streaming_with_coder_error(self, mock_get_session):
        """Test non-streaming behavior when coder fails"""
        # Mock session but make coder fail
        mock_coder = MagicMock()
        mock_io = MagicMock()
        mock_io.get_captured_output.return_value = ""
        mock_io.get_captured_errors.return_value = "Coder error"
        mock_io.get_captured_warnings.return_value = ""
        
        mock_session = {
            "coder": mock_coder,
            "io": mock_io,
            "repo_path": "/tmp/test"
        }
        
        mock_get_session.return_value = (mock_session, "test-session-id")
        
        with patch('api_server._run_coder_blocking') as mock_run_coder:
            mock_run_coder.side_effect = Exception("Coder execution failed")
            
            chat_data = {
                "message": "Test message",
                "stream": False
            }
            
            response = client.post("/chat", json=chat_data)
            
            # Should handle error gracefully
            assert response.status_code == 500


class TestStreamingPerformance:
    """Test streaming performance characteristics"""
    
    @patch('api_server.get_or_create_session')
    def test_streaming_response_timing(self, mock_get_session):
        """Test that streaming responses start quickly"""
        import time
        
        # Mock session
        mock_coder = MagicMock()
        mock_io = MagicMock()
        mock_session = {
            "coder": mock_coder,
            "io": mock_io,
            "repo_path": "/tmp/test"
        }
        mock_get_session.return_value = (mock_session, "test-session-id")
        
        chat_data = {
            "message": "Test streaming timing",
            "stream": True
        }
        
        start_time = time.time()
        response = client.post("/chat", json=chat_data)
        response_time = time.time() - start_time
        
        # Streaming should start quickly (within 1 second)
        assert response_time < 1.0
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 