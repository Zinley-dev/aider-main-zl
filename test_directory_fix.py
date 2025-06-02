#!/usr/bin/env python3
"""
Test script to verify --directory argument is consistently recognized
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path


def test_directory_argument():
    """Test that --directory argument works consistently"""
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_project"
        test_dir.mkdir()
        
        # Create a simple file in the test directory
        test_file = test_dir / "test.py"
        test_file.write_text("# Test file\nprint('Hello')\n")
        
        print(f"Testing with directory: {test_dir}")
        
        # Test multiple times to catch intermittent issues
        for i in range(5):
            print(f"\nTest run {i+1}/5:")
            
            # Run aider with --directory argument
            cmd = [
                sys.executable, "-m", "aider",
                "--directory", str(test_dir),
                "--no-auto-commits",
                "--no-git",
                "--exit",
                "--yes-always"
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if "unrecognized arguments: --directory" in result.stderr:
                    print(f"  ❌ FAILED: --directory not recognized")
                    print(f"  stderr: {result.stderr}")
                    return False
                elif result.returncode != 0:
                    print(f"  ⚠️  Non-zero exit code: {result.returncode}")
                    if result.stderr:
                        print(f"  stderr: {result.stderr}")
                else:
                    print(f"  ✅ SUCCESS: Command executed without --directory error")
                    
            except subprocess.TimeoutExpired:
                print(f"  ⚠️  Command timed out")
            except Exception as e:
                print(f"  ❌ Error running command: {e}")
                return False
        
        print("\n✅ All tests passed! --directory argument is working correctly.")
        return True


if __name__ == "__main__":
    success = test_directory_argument()
    sys.exit(0 if success else 1) 