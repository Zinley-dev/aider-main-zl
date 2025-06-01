#!/usr/bin/env python
"""Test script for the new --directory option in aider"""

import os
import sys
import tempfile
from pathlib import Path
import subprocess
import shutil

def test_directory_option():
    """Test that aider --directory works correctly"""
    
    # Create a temporary directory structure for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test project directory
        project_dir = Path(tmpdir) / "test_project"
        project_dir.mkdir()
        
        # Create a simple Python file in the project
        test_file = project_dir / "hello.py"
        test_file.write_text('print("Hello from test project!")\n')
        
        # Initialize git repo in the project directory
        subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=project_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"], 
            cwd=project_dir, 
            capture_output=True,
            env={**os.environ, "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.com",
                 "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.com"}
        )
        
        # Current directory should be somewhere else
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            # Test 1: Run aider with --directory option
            print(f"Test 1: Running aider from {os.getcwd()} with --directory {project_dir}")
            cmd = [sys.executable, "-m", "aider", "--directory", str(project_dir), "--exit", "--yes"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Test 1 passed: aider accepted --directory option")
                if "Changed working directory to:" in result.stdout:
                    print("✓ Directory change message found in output")
                else:
                    print("✗ Directory change message not found in output")
                    print(f"stdout: {result.stdout}")
            else:
                print(f"✗ Test 1 failed: aider returned code {result.returncode}")
                print(f"stdout: {result.stdout}")
                print(f"stderr: {result.stderr}")
            
            # Test 2: Test with non-existent directory
            print("\nTest 2: Testing with non-existent directory")
            fake_dir = Path(tmpdir) / "non_existent"
            cmd = [sys.executable, "-m", "aider", "--directory", str(fake_dir), "--exit", "--yes"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print("✓ Test 2 passed: aider correctly rejected non-existent directory")
                if "does not exist" in result.stderr or "does not exist" in result.stdout:
                    print("✓ Error message found in output")
                else:
                    print("✗ Expected error message not found")
            else:
                print("✗ Test 2 failed: aider should have rejected non-existent directory")
            
            # Test 3: Test with a file instead of directory
            print("\nTest 3: Testing with a file instead of directory")
            test_file_path = Path(tmpdir) / "test.txt"
            test_file_path.write_text("test")
            cmd = [sys.executable, "-m", "aider", "--directory", str(test_file_path), "--exit", "--yes"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print("✓ Test 3 passed: aider correctly rejected file as directory")
                if "is not a directory" in result.stderr or "is not a directory" in result.stdout:
                    print("✓ Error message found in output")
                else:
                    print("✗ Expected error message not found")
            else:
                print("✗ Test 3 failed: aider should have rejected file as directory")
                
        finally:
            os.chdir(original_cwd)

if __name__ == "__main__":
    print("Testing aider --directory option...")
    test_directory_option()
    print("\nTest completed!") 