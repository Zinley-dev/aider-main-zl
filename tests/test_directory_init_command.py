#!/usr/bin/env python3
"""
Unit tests for aider initialization with --directory argument
Tests the specific command: aider --directory /path --model snowx/gpt-4.1 --stream --yes --no-detect-urls
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the aider module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aider.main import main
from aider.io import InputOutput


class TestDirectoryInitCommand(unittest.TestCase):
    """Test cases for aider initialization with --directory argument"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_directory_argument_parsing(self):
        """Test that --directory argument is correctly parsed with all flags"""
        args = [
            "--directory", self.test_dir,
            "--model", "snowx/gpt-4.1",
            "--stream",
            "--yes",
            "--no-detect-urls",
            "--exit"  # Exit immediately to avoid full initialization
        ]
        
        # Create some test files in the directory
        test_file = Path(self.test_dir) / "test.py"
        test_file.write_text("print('hello world')")
        
        try:
            # Mock InputOutput to capture initialization
            with patch('aider.main.InputOutput') as mock_io_class:
                mock_io = MagicMock()
                mock_io_class.return_value = mock_io
                
                # Mock GitRepo to avoid git operations
                with patch('aider.main.GitRepo') as mock_git_repo:
                    mock_repo = MagicMock()
                    mock_git_repo.return_value = mock_repo
                    
                    # Run main with test arguments
                    result = main(args)
                    
                    # Should not raise SystemExit with error code
                    self.assertIsNone(result)
                    
        except SystemExit as e:
            # Exit code 0 is expected for --exit flag
            self.assertEqual(e.code, 0, f"Expected exit code 0, got {e.code}")

    def test_directory_argument_with_nonexistent_path(self):
        """Test error handling when --directory points to non-existent path"""
        nonexistent_path = "/path/that/does/not/exist/hopefully"
        args = [
            "--directory", nonexistent_path,
            "--model", "snowx/gpt-4.1",
            "--exit"
        ]
        
        # Should return error code 1 for non-existent directory
        result = main(args)
        self.assertEqual(result, 1)

    def test_directory_argument_with_file_instead_of_directory(self):
        """Test error handling when --directory points to a file"""
        # Create a temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b"test content")
            tmp_file_path = tmp_file.name
        
        try:
            args = [
                "--directory", tmp_file_path,
                "--model", "snowx/gpt-4.1",
                "--exit"
            ]
            
            # Should return error code 1 for file instead of directory
            result = main(args)
            self.assertEqual(result, 1)
            
        finally:
            os.unlink(tmp_file_path)

    def test_directory_equals_syntax(self):
        """Test --directory=path syntax"""
        args = [
            f"--directory={self.test_dir}",
            "--model", "snowx/gpt-4.1", 
            "--stream",
            "--yes",
            "--no-detect-urls",
            "--exit"
        ]
        
        # Create test file
        test_file = Path(self.test_dir) / "test.js"
        test_file.write_text("console.log('hello');")
        
        try:
            with patch('aider.main.InputOutput') as mock_io_class:
                mock_io = MagicMock()
                mock_io_class.return_value = mock_io
                
                with patch('aider.main.GitRepo') as mock_git_repo:
                    mock_repo = MagicMock()
                    mock_git_repo.return_value = mock_repo
                    
                    result = main(args)
                    self.assertIsNone(result)
                    
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    def test_directory_argument_changes_working_directory(self):
        """Test that --directory actually changes the working directory"""
        original_cwd = os.getcwd()
        
        args = [
            "--directory", self.test_dir,
            "--model", "test-model",
            "--exit"
        ]
        
        try:
            with patch('aider.main.InputOutput') as mock_io_class:
                mock_io = MagicMock()
                mock_io_class.return_value = mock_io
                
                with patch('aider.main.GitRepo'):
                    # After main runs with --directory, we should be in test_dir
                    main(args)
                    current_dir = os.getcwd()
                    expected_dir = str(Path(self.test_dir).resolve())
                    actual_dir = str(Path(current_dir).resolve())
                    self.assertEqual(actual_dir, expected_dir)
                    
        except SystemExit as e:
            self.assertEqual(e.code, 0)
        finally:
            # Restore original directory
            os.chdir(original_cwd)

    def test_all_flags_combination(self):
        """Test the exact command combination from the user"""
        # Use a real directory that exists
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            args = [
                "--directory", temp_dir,
                "--model", "snowx/gpt-4.1",
                "--stream",
                "--yes", 
                "--no-detect-urls",
                "--exit"  # Exit to avoid full execution
            ]
            
            # Create a sample file to work with
            sample_file = Path(temp_dir) / "app.py"
            sample_file.write_text("""
def main():
    print("Hello from app!")

if __name__ == "__main__":
    main()
""")
            
            try:
                with patch('aider.main.InputOutput') as mock_io_class:
                    mock_io = MagicMock()
                    mock_io_class.return_value = mock_io
                    
                    with patch('aider.main.GitRepo') as mock_git_repo:
                        mock_repo = MagicMock()
                        mock_git_repo.return_value = mock_repo
                        
                        # This should not raise any argument parsing errors
                        result = main(args)
                        self.assertIsNone(result)
                        
            except SystemExit as e:
                # --exit flag should cause clean exit with code 0
                self.assertEqual(e.code, 0, f"Expected clean exit, got code {e.code}")

    def test_argument_parsing_robustness(self):
        """Test that argument parsing is robust and handles edge cases"""
        test_cases = [
            # Basic case
            ["--directory", self.test_dir, "--model", "test-model", "--exit"],
            # Equals syntax
            [f"--directory={self.test_dir}", "--model", "test-model", "--exit"],
            # With multiple flags
            ["--directory", self.test_dir, "--model", "snowx/gpt-4.1", "--stream", "--yes", "--exit"],
            # Different order
            ["--model", "test-model", "--directory", self.test_dir, "--exit"],
        ]
        
        for i, args in enumerate(test_cases):
            with self.subTest(f"Test case {i+1}: {args}"):
                try:
                    with patch('aider.main.InputOutput') as mock_io_class:
                        mock_io = MagicMock()
                        mock_io_class.return_value = mock_io
                        
                        with patch('aider.main.GitRepo'):
                            result = main(args)
                            # Should not return error
                            self.assertIsNone(result)
                            
                except SystemExit as e:
                    # Clean exit is acceptable
                    self.assertEqual(e.code, 0)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)