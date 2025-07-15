#!/usr/bin/env python
"""Test to verify InputOutput scope fix works properly"""
import subprocess
import sys
import tempfile
from pathlib import Path

def test_directory_with_inputoutput():
    """Test that --directory doesn't cause InputOutput scope errors"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir) / "test_project"
        target_dir.mkdir()
        
        # Run aider with --directory argument
        cmd = [
            sys.executable, "aider/main.py",
            "--directory", str(target_dir),
            "--help"  # Just run help to test the basic functionality
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check for the NameError we were seeing
        if "NameError: cannot access free variable 'InputOutput'" in result.stderr:
            print("✗ ERROR: Still getting InputOutput NameError")
            print("STDERR:")
            print(result.stderr)
            return False
        
        # Check that help output is shown (basic functionality works)
        if "usage: aider" in result.stdout or "usage: main.py" in result.stdout:
            print("✓ Help output shown, no InputOutput errors")
            return True
        else:
            print("✗ ERROR: Unexpected output")
            print("STDOUT:")
            print(result.stdout)
            print("STDERR:")
            print(result.stderr)
            return False

if __name__ == "__main__":
    print("Testing InputOutput scope fix...")
    success = test_directory_with_inputoutput()
    
    if success:
        print("\n✓ Test passed! No InputOutput scope errors.")
    else:
        print("\n✗ Test failed!")
    
    sys.exit(0 if success else 1) 