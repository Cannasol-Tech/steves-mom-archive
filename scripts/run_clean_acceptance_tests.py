#!/usr/bin/env python3
"""
Clean acceptance test runner.

This script runs behave tests with clean, formatted output and provides
a professional testing experience.
"""
import subprocess
import sys
import time
from pathlib import Path

# Ensure both the project root and the scripts directory are on sys.path
_SCRIPTS_DIR = Path(__file__).parent
_PROJECT_ROOT = _SCRIPTS_DIR.parent
for _p in (str(_SCRIPTS_DIR), str(_PROJECT_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Import the formatter from the scripts directory without requiring package semantics
try:
    from clean_test_output import TestOutputFormatter
except Exception as _imp_err:  # pragma: no cover
    print(f"[WARN] Failed to import TestOutputFormatter: {_imp_err}")
    # Minimal fallback to avoid hard-failure; output will be plain
    class TestOutputFormatter:  # type: ignore
        def __init__(self, *_, **__):
            pass
        def print_header(self, title: str, emoji: str = ""): print(f"\n{emoji} {title}")
        def print_step(self, message: str, emoji: str = ""): print(f"{emoji} {message}...")
        def print_success(self, message: str, emoji: str = ""): print(f"{emoji} {message}")
        def print_warning(self, message: str, emoji: str = ""): print(f"{emoji} {message}")
        def print_error(self, message: str, emoji: str = ""): print(f"{emoji} {message}")
        def print_info(self, message: str, emoji: str = ""): print(f"{emoji} {message}")
        def print_summary_box(self, title, content):
            print(f"\n{title}")
            for k, v in (content or {}).items():
                print(f" - {k}: {v}")
        def format_behave_results(self, behave_output: str):
            return {"Raw Output": behave_output.splitlines()[-1] if behave_output else ""}
        def format_executive_report(self, *_):
            return None


def run_command_quietly(cmd: list, capture_output: bool = True) -> tuple[int, str, str]:
    """Run a command and optionally capture its output."""
    try:
        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, cwd=Path.cwd())
            return result.returncode, "", ""
    except Exception as e:
        return 1, "", str(e)


def main():
    """Main entry point for clean acceptance test runner."""
    formatter = TestOutputFormatter()
    
    # Print header
    formatter.print_header("Steve's Mom AI - Acceptance Tests", "🧪")
    
    # Step 1: Setup dependencies quietly
    formatter.print_step("Preparing test environment", "⚙️")
    
    # Run setup-backend quietly
    setup_cmd = ["make", "setup-backend"]
    exit_code, stdout, stderr = run_command_quietly(setup_cmd)
    
    if exit_code != 0:
        formatter.print_error("Failed to setup backend dependencies")
        if stderr:
            print(f"Error: {stderr}")
        sys.exit(1)
    
    # Run setup-dev quietly
    setup_dev_cmd = ["make", "setup-dev"]
    exit_code, stdout, stderr = run_command_quietly(setup_dev_cmd)
    
    if exit_code != 0:
        formatter.print_error("Failed to setup development dependencies")
        if stderr:
            print(f"Error: {stderr}")
        sys.exit(1)
    
    formatter.print_success("Dependencies ready")
    
    # Step 2: Create directories
    formatter.print_step("Preparing test directories", "📁")
    Path("tests/acceptance/features").mkdir(parents=True, exist_ok=True)
    Path("final").mkdir(exist_ok=True)
    
    # Step 3: Run behave tests
    formatter.print_step("Running acceptance tests", "🎯")
    
    behave_cmd = [
        ".venv/bin/behave",
        "-f", "json",
        "-o", "tests/acceptance/.behave-report.json",
        "tests/acceptance/features"
    ]
    
    # Set environment variable to disable pytest plugin autoload
    import os
    env = os.environ.copy()
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    
    start_time = time.time()
    
    try:
        # Run behave and capture both JSON and console output
        result = subprocess.run(
            behave_cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
            env=env
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        behave_exit_code = result.returncode
        behave_output = result.stdout
        behave_errors = result.stderr
        
    except Exception as e:
        formatter.print_error(f"Failed to run behave tests: {e}")
        sys.exit(1)
    
    # Step 4: Generate executive report
    formatter.print_step("Generating executive report", "📊")
    
    exec_report_cmd = [
        ".venv/bin/python",
        "scripts/acceptance_to_executive_report.py",
        "--behave-json", "tests/acceptance/.behave-report.json",
        "--out", "final/executive-report.json"
    ]
    
    env_vars = {
        "REPORT_OWNER": "Cannasol-Tech",
        "REPORT_REPO": "steves-mom-archive"
    }
    
    exec_env = os.environ.copy()
    exec_env.update(env_vars)
    
    exec_exit_code, exec_stdout, exec_stderr = run_command_quietly(exec_report_cmd)
    
    if exec_exit_code == 0:
        formatter.print_success("Executive report generated")
    else:
        formatter.print_warning("Executive report generation had issues")
    
    # Step 5: Parse and display results
    if behave_output:
        # Parse behave output for summary
        results = formatter.format_behave_results(behave_output)
        results["Duration"] = f"{duration:.1f}s"
        
        # Print clean summary
        formatter.print_summary_box("Test Results Summary", results)
        
        # Check for executive report
        exec_report_path = Path("final/executive-report.json")
        exec_results = formatter.format_executive_report(exec_report_path)
        
        if exec_results:
            formatter.print_summary_box("Executive Report", exec_results)
        
        # Print final status
        if behave_exit_code == 0:
            formatter.print_success("All acceptance tests passed! 🎉")
            formatter.print_info(f"Executive report: {exec_report_path}")
        else:
            formatter.print_error("Some tests failed")
            if behave_errors:
                print(f"\nErrors:\n{behave_errors}")
    
    else:
        formatter.print_error("No test output received")
        if behave_errors:
            print(f"Errors:\n{behave_errors}")
    
    # Ensure executive report exists even on failure
    exec_report_path = Path("final/executive-report.json")
    if not exec_report_path.exists():
        fallback_report = {
            "version": "1.0.0",
            "owner": "Cannasol-Tech",
            "repo": "steves-mom-archive",
            "releaseTag": "local",
            "commit": "unknown",
            "createdAt": "",
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "durationMs": 0
            },
            "scenarios": [],
            "requirements": []
        }
        
        import json
        with open(exec_report_path, 'w') as f:
            json.dump(fallback_report, f, indent=2)
    
    # Exit with behave's exit code
    sys.exit(behave_exit_code)


if __name__ == '__main__':
    main()
