#!/usr/bin/env python3
"""
Unit tests for Aider REST API using pytest and FastAPI TestClient
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path

from fastapi.testclient import TestClient
from api_server import app, parse_and_apply_search_replace, simple_search_replace_parser

# Test client
client = TestClient(app)

class TestHealthAndModels:
    """Test basic endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_list_models(self):
        """Test models endpoint"""
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()
        assert "openai" in data
        assert "anthropic" in data
        assert "aliases" in data


class TestSessionManagement:
    """Test session-related endpoints"""
    
    def test_create_session(self):
        """Test session creation"""
        response = client.post("/sessions", json={})
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["session_id"] is not None
        assert len(data["session_id"]) == 36  # UUID length
        return data["session_id"]
    
    def test_create_session_with_params(self):
        """Test session creation with parameters"""
        session_data = {
            "model": "gpt-4o",
            "edit_format": "diff",
            "auto_commits": False
        }
        response = client.post("/sessions", json=session_data)
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "gpt-4o"
        assert "session_id" in data
    
    def test_delete_session(self):
        """Test session deletion"""
        # Create session first
        create_response = client.post("/sessions", json={})
        session_id = create_response.json()["session_id"]
        
        # Delete session
        response = client.delete(f"/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_delete_nonexistent_session(self):
        """Test deleting non-existent session"""
        fake_session_id = "non-existent-session-id"
        response = client.delete(f"/sessions/{fake_session_id}")
        assert response.status_code == 404


class TestSearchReplaceParser:
    """Test SEARCH/REPLACE parsing functionality"""
    
    def test_simple_search_replace_parser(self):
        """Test simple parser with valid SEARCH/REPLACE blocks"""
        response = """
<<<<<<< SEARCH
def hello():
    print("Hello")
=======
def hello():
    print("Hello, World!")
>>>>>>> REPLACE
"""
        
        result = simple_search_replace_parser(response)
        assert len(result) == 1
        search, replace = result[0]
        assert "Hello" in search
        assert "Hello, World!" in replace
    
    def test_multiple_search_replace_blocks(self):
        """Test parser with multiple SEARCH/REPLACE blocks"""
        response = """
<<<<<<< SEARCH
def func1():
    pass
=======
def func1():
    return "modified"
>>>>>>> REPLACE

<<<<<<< SEARCH
def func2():
    pass
=======
def func2():
    return "also modified"
>>>>>>> REPLACE
"""
        
        result = simple_search_replace_parser(response)
        assert len(result) == 2
        assert "func1" in result[0][0]
        assert "func2" in result[1][0]
    
    def test_search_replace_with_no_blocks(self):
        """Test parser with response containing no SEARCH/REPLACE blocks"""
        response = "This is just a regular response with no search/replace blocks."
        result = simple_search_replace_parser(response)
        assert len(result) == 0

    def test_parse_and_apply_search_replace(self):
        """Test full parse and apply functionality"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""def hello():
    print("Hello")

def goodbye():
    print("Goodbye")
""")
            temp_file = f.name
        
        try:
            response = """
<<<<<<< SEARCH
def hello():
    print("Hello")
=======
def hello():
    print("Hello, World!")
>>>>>>> REPLACE
"""
            
            result = parse_and_apply_search_replace(response, temp_file)
            
            # Check that the replacement was made
            assert "Hello, World!" in result
            assert "def hello():" in result
            assert "def goodbye():" in result  # Other content should remain
            
        finally:
            os.unlink(temp_file)
    
    def test_parse_and_apply_with_invalid_file(self):
        """Test parse and apply with non-existent file"""
        response = """
<<<<<<< SEARCH
old content
=======
new content
>>>>>>> REPLACE
"""
        
        result = parse_and_apply_search_replace(response, "/non/existent/file.txt")
        assert result == ""  # Should return empty string for non-existent file


class TestFileOperations:
    """Test file-related operations"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.html")
        with open(self.test_file, 'w') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <h1>Original Title</h1>
</body>
</html>""")
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_sync_file_create_new(self):
        """Test syncing content to create new file"""
        session_data = {"repo_path": self.temp_dir}
        session_response = client.post("/sessions", json=session_data)
        session_id = session_response.json()["session_id"]
        
        sync_data = {
            "session_id": session_id,
            "file_path": "new_file.txt",
            "content": "This is new content",
            "create_if_not_exists": True
        }
        
        response = client.post("/sync_file", json=sync_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["was_created"] is True
        
        # Verify file was created
        new_file_path = os.path.join(self.temp_dir, "new_file.txt")
        assert os.path.exists(new_file_path)
        with open(new_file_path, 'r') as f:
            assert f.read() == "This is new content"
    
    def test_sync_file_update_existing(self):
        """Test syncing content to update existing file"""
        session_data = {"repo_path": self.temp_dir}
        session_response = client.post("/sessions", json=session_data)
        session_id = session_response.json()["session_id"]
        
        sync_data = {
            "session_id": session_id,
            "file_path": "test.html",
            "content": "Updated content",
            "create_if_not_exists": False
        }
        
        response = client.post("/sync_file", json=sync_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["was_created"] is False
        
        # Verify file was updated
        with open(self.test_file, 'r') as f:
            assert f.read() == "Updated content"


class TestChatFunctionality:
    """Test chat endpoints (mocked)"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "index.html")
        with open(self.test_file, 'w') as f:
            f.write("""<!DOCTYPE html>
<html>
<body>
    <h1>Hello World</h1>
</body>
</html>""")
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('api_server._run_coder_blocking')
    @patch('api_server.get_or_create_session')
    def test_chat_non_stream(self, mock_get_session, mock_run_coder):
        """Test non-streaming chat functionality"""
        # Mock session
        mock_coder = MagicMock()
        mock_io = MagicMock()
        mock_io.get_captured_output.return_value = ""
        mock_io.get_captured_errors.return_value = ""
        mock_io.get_captured_warnings.return_value = ""
        mock_io.read_text.return_value = "file content"
        
        mock_session = {
            "coder": mock_coder,
            "io": mock_io,
            "repo_path": self.temp_dir
        }
        
        mock_get_session.return_value = (mock_session, "test-session-id")
        mock_run_coder.return_value = "AI response"
        
        # Set up coder mock
        mock_coder.aider_edited_files = {self.test_file}
        mock_coder.get_rel_fname.return_value = "index.html"
        mock_coder.message_tokens_sent = 100
        mock_coder.message_tokens_received = 50
        mock_coder.message_cost = 0.001
        
        chat_data = {
            "message": "Change the title to 'Welcome'",
            "files": ["index.html"],
            "stream": False
        }
        
        response = client.post("/chat", json=chat_data)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert data["session_id"] == "test-session-id"
    
    def test_chat_request_validation(self):
        """Test chat request validation"""
        # Test with empty message
        response = client.post("/chat", json={"message": ""})
        assert response.status_code == 422  # Validation error
        
        # Test with invalid stream parameter
        response = client.post("/chat", json={
            "message": "test",
            "stream": "invalid"
        })
        assert response.status_code == 422


class TestFileUpload:
    """Test file upload functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_upload_text_file(self):
        """Test uploading a text file"""
        # Create session with specific repo_path
        session_data = {"repo_path": self.temp_dir}
        session_response = client.post("/sessions", json=session_data)
        session_id = session_response.json()["session_id"]
        
        # Create test file content
        file_content = b"def hello():\n    print('Hello World')"
        
        # Upload file
        files = {"file": ("test.py", file_content, "text/plain")}
        data = {"session_id": session_id, "add_to_chat": "true"}
        
        response = client.post("/upload_file", files=files, data=data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "test.py" in response_data["file_path"]
        assert response_data["file_type"] == "text"


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_invalid_session_id(self):
        """Test operations with invalid session ID"""
        invalid_id = "invalid-session-id"
        
        # Test get files with invalid session
        response = client.get(f"/sessions/{invalid_id}/files")
        assert response.status_code == 404
        
        # Test clear chat with invalid session
        response = client.post(f"/sessions/{invalid_id}/clear_chat")
        assert response.status_code == 404
    
    def test_missing_required_fields(self):
        """Test requests with missing required fields"""
        # Test sync_file without session_id
        response = client.post("/sync_file", json={
            "file_path": "test.txt",
            "content": "content"
        })
        assert response.status_code == 422
        
        # Test upload_file without file
        response = client.post("/upload_file", data={"session_id": "test"})
        assert response.status_code == 422


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 