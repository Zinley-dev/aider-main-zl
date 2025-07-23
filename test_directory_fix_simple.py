#!/usr/bin/env python3
"""
Simple test to verify --directory argument is consistently recognized
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path

def test_directory_argument():
    """Test that --directory argument works with your exact command format"""
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as test_dir:
        print(f"Testing with directory: {test_dir}")
        
        # Test with your exact arguments (but using test directory and adding --help to avoid full execution)
        cmd = [
            sys.executable, "-m", "aider",
            "--directory", test_dir,
            "--model", "snowx/gpt-4.1",
            "--stream",
            "--yes",
            "--no-detect-urls",
            "--help"
        ]
        
        print("Running command:", " ".join(cmd))
        
        try:
            result = subprocess.run(
                cmd,
                cwd="/Users/khoinguyen/Downloads/aider-main-zl",
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Check if the command succeeded (--help should exit with code 0)
            if result.returncode == 0:
                print("✅ SUCCESS: Command executed without --directory error")
                print("Help output received correctly")
                return True
            else:
                print(f"❌ FAILED: Command returned exit code {result.returncode}")
                if "unrecognized arguments: --directory" in result.stderr:
                    print("  ERROR: --directory not recognized")
                print("STDERR:", result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ FAILED: Command timed out")
            return False
        except Exception as e:
            print(f"❌ FAILED: Exception occurred: {e}")
            return False

if __name__ == "__main__":
    print("Testing --directory argument fix...")
    success = test_directory_argument()
    
    if success:
        print("\n✅ Test PASSED! --directory argument is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Test FAILED! --directory argument still has issues.")
        sys.exit(1)