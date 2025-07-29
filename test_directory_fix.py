#!/usr/bin/env python3
"""
Test script to verify --directory argument fixes work correctly
"""

import os
import sys
import tempfile
from pathlib import Path

# Add aider to path
sys.path.insert(0, str(Path(__file__).parent))

from aider.main import main


def test_directory_argument():
    """Test that --directory argument works consistently"""
    print("Testing --directory argument fix...")
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_project"
        test_dir.mkdir()
        
        # Create a marker file to verify we're in the right directory
        marker_file = test_dir / ".aider_test_marker"
        marker_file.write_text("test_marker")
        
        original_cwd = os.getcwd()
        
        try:
            # Test multiple times to catch intermittent issues
            for i in range(10):
                print(f"  Test iteration {i+1}/10... ", end="")
                
                # Reset to original directory
                os.chdir(original_cwd)
                
                # Test the --directory argument
                argv = [
                    "--directory", str(test_dir),
                    "--no-auto-commits",
                    "--no-git",
                    "--exit", 
                    "--yes-always"
                ]
                
                try:
                    result = main(argv=argv)
                    
                    # Check if we're in the correct directory
                    current_dir = Path.cwd()
                    marker_exists = (current_dir / ".aider_test_marker").exists()
                    
                    if result == 0 and marker_exists:
                        print("✓ PASS")
                    else:
                        print(f"✗ FAIL (result={result}, marker_exists={marker_exists})")
                        return False
                        
                except Exception as e:
                    print(f"✗ FAIL (exception: {e})")
                    return False
            
            print("✓ All tests passed!")
            return True
            
        finally:
            # Always restore original directory
            os.chdir(original_cwd)


if __name__ == "__main__":
    print("=" * 60)
    print("Testing --directory argument robustness fixes")
    print("=" * 60)
    
    try:
        if test_directory_argument():
            print("🎉 Test passed! The --directory fix appears to be working.")
            sys.exit(0)
        else:
            print("❌ Test failed. The fix may need more work.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        sys.exit(1)