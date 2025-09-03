#!/usr/bin/env python3
"""
Test runner for Steve's Mom AI Chatbot

This script runs all tests and provides a summary of results.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 1.0.0
"""

import sys
import subprocess
import os
from pathlib import Path

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def log_info(message):
    print(f"{BLUE}[INFO]{NC} {message}")

def log_success(message):
    print(f"{GREEN}[SUCCESS]{NC} {message}")

def log_warning(message):
    print(f"{YELLOW}[WARNING]{NC} {message}")

def log_error(message):
    print(f"{RED}[ERROR]{NC} {message}")

def run_tests():
    """Run all tests and return results."""
    project_root = Path(__file__).parent.parent
    
    log_info("Starting test suite for Steve's Mom AI Chatbot")
    log_info(f"Project root: {project_root}")
    
    # Check if pytest is available
    try:
        import pytest
        log_success("pytest is available")
    except ImportError:
        log_error("pytest is not installed. Please install it with: pip install pytest")
        return False
    
    # Run sanity tests
    log_info("Running sanity tests...")
    sanity_test_path = project_root / "tests" / "unit" / "test_sanity.py"
    
    if not sanity_test_path.exists():
        log_error(f"Sanity test file not found: {sanity_test_path}")
        return False
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(sanity_test_path), 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], capture_output=True, text=True, cwd=project_root)
        
        print("\n" + "="*60)
        print("TEST OUTPUT")
        print("="*60)
        print(result.stdout)
        
        if result.stderr:
            print("\n" + "="*60)
            print("TEST ERRORS/WARNINGS")
            print("="*60)
            print(result.stderr)
        
        if result.returncode == 0:
            log_success("All tests passed!")
            return True
        else:
            log_warning(f"Some tests failed or were skipped (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        log_error(f"Error running tests: {e}")
        return False

def check_project_structure():
    """Check that project has expected structure."""
    project_root = Path(__file__).parent.parent
    
    log_info("Checking project structure...")
    
    expected_files = [
        "backend/models/ai_models.py",
        "backend/ai/steves_mom_agent.py", 
        "backend/functions/chat_function.py",
        "backend/requirements.txt",
        "tests/unit/test_sanity.py"
    ]
    
    missing_files = []
    for file_path in expected_files:
        full_path = project_root / file_path
        if full_path.exists():
            log_success(f"✓ {file_path}")
        else:
            log_warning(f"✗ {file_path} (missing)")
            missing_files.append(file_path)
    
    if missing_files:
        log_warning(f"Missing {len(missing_files)} expected files")
        return False
    else:
        log_success("All expected files present")
        return True

def check_dependencies():
    """Check that key dependencies are available."""
    log_info("Checking Python dependencies...")
    
    required_packages = [
        "pytest",
        "pydantic", 
        "langchain",
        "openai",
        "tiktoken"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            log_success(f"✓ {package}")
        except ImportError:
            log_warning(f"✗ {package} (not installed)")
            missing_packages.append(package)
    
    if missing_packages:
        log_warning(f"Missing {len(missing_packages)} required packages")
        log_info("Install missing packages with:")
        log_info(f"pip install {' '.join(missing_packages)}")
        return False
    else:
        log_success("All required packages available")
        return True

def main():
    """Main test runner."""
    print(f"{BLUE}{'='*60}{NC}")
    print(f"{BLUE}Steve's Mom AI Chatbot - Test Suite{NC}")
    print(f"{BLUE}{'='*60}{NC}")
    
    # Check project structure
    structure_ok = check_project_structure()
    print()
    
    # Check dependencies
    deps_ok = check_dependencies()
    print()
    
    # Run tests
    if structure_ok and deps_ok:
        tests_ok = run_tests()
    else:
        log_warning("Skipping tests due to missing files or dependencies")
        tests_ok = False
    
    # Summary
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}TEST SUMMARY{NC}")
    print(f"{BLUE}{'='*60}{NC}")
    
    if structure_ok:
        log_success("✓ Project structure")
    else:
        log_error("✗ Project structure")
    
    if deps_ok:
        log_success("✓ Dependencies")
    else:
        log_error("✗ Dependencies")
    
    if tests_ok:
        log_success("✓ Tests")
    else:
        log_error("✗ Tests")
    
    overall_success = structure_ok and deps_ok and tests_ok
    
    if overall_success:
        log_success("🎉 All checks passed! System is ready.")
        return 0
    else:
        log_warning("⚠️  Some checks failed. Review output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
