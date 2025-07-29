#!/usr/bin/env python3
"""
Simple test to verify --directory argument parsing without full main() execution
"""

import sys
import tempfile
from pathlib import Path

# Add aider to path
sys.path.insert(0, str(Path(__file__).parent))

from aider.args import get_parser


def test_directory_argument_parsing():
    """Test that --directory argument is parsed correctly"""
    print("Testing --directory argument parsing...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_project"
        test_dir.mkdir()
        
        # Test different argument formats
        test_cases = [
            ["--directory", str(test_dir), "--exit"],
            [f"--directory={test_dir}", "--exit"],
            ["--exit", "--directory", str(test_dir)],
        ]
        
        for i, argv in enumerate(test_cases, 1):
            print(f"  Test case {i}: {' '.join(argv[:2])}... ", end="")
            
            try:
                parser = get_parser([], None)
                args = parser.parse_args(argv)
                
                # Check that directory argument was parsed
                if hasattr(args, 'directory') and args.directory:
                    print("✓ PASS")
                else:
                    print(f"✗ FAIL (directory={getattr(args, 'directory', 'MISSING')})")
                    return False
                    
            except Exception as e:
                print(f"✗ FAIL (exception: {e})")
                return False
        
        print("✓ All parsing tests passed!")
        return True


def test_directory_argument_consistency():
    """Test multiple parsing attempts for consistency"""
    print("Testing --directory parsing consistency...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_project" 
        test_dir.mkdir()
        
        argv = ["--directory", str(test_dir), "--exit", "--no-git"]
        
        # Test multiple parser instances to catch state issues
        for i in range(20):
            print(f"  Iteration {i+1}/20... ", end="")
            
            try:
                parser = get_parser([], None)
                args = parser.parse_args(argv)
                
                if hasattr(args, 'directory') and args.directory == str(test_dir):
                    print("✓")
                else:
                    print(f"✗ FAIL (got: {getattr(args, 'directory', 'MISSING')})")
                    return False
                    
            except Exception as e:
                print(f"✗ FAIL (exception: {e})")
                return False
        
        print("✓ All consistency tests passed!")
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("Testing --directory argument parsing fixes")
    print("=" * 60)
    
    tests = [
        test_directory_argument_parsing,
        test_directory_argument_consistency
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The --directory argument parsing is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed.")
        sys.exit(1)