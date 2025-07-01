#!/usr/bin/env python3
"""
Test runner script for Aider REST API
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle output"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            return False
            
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking test dependencies...")
    
    required_packages = [
        "pytest",
        "fastapi",
        "httpx",  # Required by TestClient
        "python-multipart",  # Required for file upload tests
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("📦 Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All dependencies are installed")
    return True

def run_all_tests():
    """Run all test suites"""
    print("🚀 Starting Aider REST API Test Suite")
    print(f"Working directory: {os.getcwd()}")
    
    # Check dependencies first
    if not check_dependencies():
        return False
    
    test_files = [
        ("test_api_unit.py", "Unit Tests"),
        ("test_search_replace.py", "Search/Replace Tests"),
        ("test_api_streaming.py", "Streaming Tests"),
    ]
    
    results = []
    
    for test_file, description in test_files:
        if Path(test_file).exists():
            command = f"python -m pytest {test_file} -v --tb=short"
            success = run_command(command, description)
            results.append((description, success))
        else:
            print(f"⚠️  Test file {test_file} not found, skipping...")
            results.append((description, None))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    failed = 0
    skipped = 0
    
    for description, result in results:
        if result is True:
            print(f"✅ {description}")
            passed += 1
        elif result is False:
            print(f"❌ {description}")
            failed += 1
        else:
            print(f"⚠️  {description} (skipped)")
            skipped += 1
    
    total = passed + failed
    if total > 0:
        success_rate = (passed / total) * 100
        print(f"\n📈 Success Rate: {success_rate:.1f}% ({passed}/{total})")
    
    if skipped > 0:
        print(f"⚠️  Skipped: {skipped}")
    
    return failed == 0

def run_specific_test(test_pattern):
    """Run specific test matching pattern"""
    command = f"python -m pytest -k '{test_pattern}' -v --tb=short"
    return run_command(command, f"Tests matching '{test_pattern}'")

def run_coverage():
    """Run tests with coverage report"""
    print("📊 Running tests with coverage...")
    
    try:
        import coverage
    except ImportError:
        print("❌ Coverage not installed. Install with: pip install coverage")
        return False
    
    commands = [
        "coverage run -m pytest test_api_unit.py test_search_replace.py test_api_streaming.py",
        "coverage report -m",
        "coverage html"
    ]
    
    for cmd in commands:
        success = run_command(cmd, f"Coverage: {cmd}")
        if not success:
            return False
    
    print("📊 Coverage report generated in htmlcov/index.html")
    return True

def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "all":
            success = run_all_tests()
            sys.exit(0 if success else 1)
        
        elif command == "coverage":
            success = run_coverage()
            sys.exit(0 if success else 1)
        
        elif command.startswith("test_"):
            # Run specific test file
            if Path(command).exists():
                success = run_command(f"python -m pytest {command} -v", f"Test file: {command}")
                sys.exit(0 if success else 1)
            else:
                print(f"❌ Test file {command} not found")
                sys.exit(1)
        
        else:
            # Run tests matching pattern
            success = run_specific_test(command)
            sys.exit(0 if success else 1)
    
    else:
        print("""
🧪 Aider REST API Test Runner

Usage:
    python run_tests.py all                    # Run all tests
    python run_tests.py coverage               # Run with coverage
    python run_tests.py test_api_unit.py       # Run specific test file
    python run_tests.py search_replace         # Run tests matching pattern
    python run_tests.py streaming              # Run streaming tests

Examples:
    python run_tests.py all
    python run_tests.py test_search
    python run_tests.py streaming
""")

if __name__ == "__main__":
    main() 