"""
Unit tests for --directory argument handling
"""

import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch

from aider.main import main


class TestDirectoryArgument:
    """Test cases for --directory argument"""
    
    def test_directory_argument_recognized(self):
        """Test that --directory argument is always recognized"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test_project"
            test_dir.mkdir()
            
            # Create a test file
            test_file = test_dir / "test.py"
            test_file.write_text("# Test file\n")
            
            # Mock sys.argv to simulate command line input
            argv = [
                "--directory", str(test_dir),
                "--no-auto-commits",
                "--no-git",
                "--exit",
                "--yes-always"
            ]
            
            # Run main and ensure no error about unrecognized --directory
            with patch('sys.stderr') as mock_stderr:
                result = main(argv=argv)
                
                # Check that there's no "unrecognized arguments: --directory" error
                if mock_stderr.write.called:
                    stderr_output = ''.join(call[0][0] for call in mock_stderr.write.call_args_list)
                    assert "--directory" not in stderr_output or "unrecognized" not in stderr_output
    
    def test_directory_argument_changes_cwd(self):
        """Test that --directory actually changes the working directory"""
        original_cwd = os.getcwd()
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                test_dir = Path(tmpdir) / "test_project"
                test_dir.mkdir()
                
                # Create marker file to verify we're in the right directory
                marker_file = test_dir / ".aider_test_marker"
                marker_file.write_text("test")
                
                argv = [
                    "--directory", str(test_dir),
                    "--no-auto-commits", 
                    "--no-git",
                    "--exit",
                    "--yes-always"
                ]
                
                # Run main
                main(argv=argv)
                
                # After main runs with --directory, we should be in test_dir
                # Check if marker file exists in current directory
                assert Path(".aider_test_marker").exists(), "Directory was not changed correctly"
                
        finally:
            # Restore original directory
            os.chdir(original_cwd)
    
    def test_directory_with_equals_syntax(self):
        """Test --directory=path syntax"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test_project"
            test_dir.mkdir()
            
            argv = [
                f"--directory={test_dir}",
                "--no-auto-commits",
                "--no-git",
                "--exit", 
                "--yes-always"
            ]
            
            with patch('sys.stderr') as mock_stderr:
                result = main(argv=argv)
                
                # Check that there's no error about unrecognized --directory
                if mock_stderr.write.called:
                    stderr_output = ''.join(call[0][0] for call in mock_stderr.write.call_args_list)
                    assert "--directory" not in stderr_output or "unrecognized" not in stderr_output
    
    def test_directory_nonexistent(self):
        """Test error handling for non-existent directory"""
        argv = [
            "--directory", "/path/that/does/not/exist",
            "--exit",
            "--yes-always"
        ]
        
        # Should return error code
        result = main(argv=argv)
        assert result == 1
    
    def test_directory_file_instead_of_dir(self):
        """Test error handling when --directory points to a file"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            try:
                argv = [
                    "--directory", tmp_file.name,
                    "--exit",
                    "--yes-always"
                ]
                
                # Should return error code
                result = main(argv=argv)
                assert result == 1
            finally:
                os.unlink(tmp_file.name) 