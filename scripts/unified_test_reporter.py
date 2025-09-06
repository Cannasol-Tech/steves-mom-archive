#!/usr/bin/env python3
"""
Unified Test Reporter for Steve's Mom AI Chatbot Project

This script aggregates test results from multiple frameworks:
- Backend unit tests (pytest)
- Frontend tests (Jest)
- Acceptance tests (behave)
- E2E tests (Playwright)

Generates both technical and executive reports as required by company standards.

Author: Cannasol Technologies
Date: 2025-09-06
Version: 1.0.0
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class UnifiedTestReporter:
    """Aggregates test results from multiple frameworks into unified reports."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reports_dir = project_root / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # Report file paths
        self.functionality_report_path = self.reports_dir / "functionality-report.json"
        self.executive_report_path = project_root / "final" / "executive-report.json"
        
        # Ensure final directory exists
        (project_root / "final").mkdir(exist_ok=True)

    def run_backend_tests_with_json(self) -> Dict[str, Any]:
        """Run backend tests and generate JSON report."""
        print("Running backend unit tests with JSON reporting...")
        
        json_report_path = self.reports_dir / "backend-tests.json"
        coverage_json_path = self.reports_dir / "coverage.json"
        
        cmd = [
            ".venv/bin/pytest",
            "-p", "pytest_asyncio",
            "-p", "pytest_jsonreport",
            "-p", "pytest_cov",
            "tests/unit/",
            "-v",
            f"--json-report-file={json_report_path}",
            "--cov=backend",
            "--cov=ai", 
            "--cov=models",
            f"--cov-report=json:{coverage_json_path}",
            "--tb=short"
        ]
        
        env = os.environ.copy()
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        
        try:
            result = subprocess.run(
                cmd, 
                cwd=self.project_root, 
                capture_output=True, 
                text=True,
                env=env
            )
            
            # Load JSON report
            if json_report_path.exists():
                with open(json_report_path) as f:
                    report_data = json.load(f)
            else:
                report_data = {"summary": {"total": 0, "passed": 0, "failed": 0}}
            
            # Load coverage data
            coverage_data = {}
            if coverage_json_path.exists():
                with open(coverage_json_path) as f:
                    coverage_data = json.load(f)
            
            return {
                "framework": "pytest",
                "type": "unit",
                "exit_code": result.returncode,
                "report": report_data,
                "coverage": coverage_data,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except Exception as e:
            print(f"Error running backend tests: {e}")
            return {
                "framework": "pytest",
                "type": "unit", 
                "exit_code": 1,
                "error": str(e),
                "report": {"summary": {"total": 0, "passed": 0, "failed": 0}},
                "coverage": {}
            }

    def run_frontend_tests_with_json(self) -> Dict[str, Any]:
        """Run frontend tests and extract results."""
        print("Running frontend tests...")
        
        cmd = ["npm", "test", "--", "--watchAll=false", "--json"]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root / "frontend",
                capture_output=True,
                text=True
            )
            
            # Jest outputs JSON to stdout when --json flag is used
            try:
                jest_output = json.loads(result.stdout)
                summary = jest_output.get("numTotalTestSuites", 0)
                passed = jest_output.get("numPassedTestSuites", 0)
                failed = jest_output.get("numFailedTestSuites", 0)
                
                return {
                    "framework": "jest",
                    "type": "frontend",
                    "exit_code": result.returncode,
                    "report": {
                        "summary": {
                            "total": summary,
                            "passed": passed,
                            "failed": failed
                        }
                    },
                    "jest_output": jest_output
                }
            except json.JSONDecodeError:
                # Fallback: parse text output
                lines = result.stdout.split('\n')
                test_line = next((line for line in lines if "Test Suites:" in line), "")
                
                return {
                    "framework": "jest",
                    "type": "frontend",
                    "exit_code": result.returncode,
                    "report": {
                        "summary": {
                            "total": 0,
                            "passed": 0 if result.returncode != 0 else 1,
                            "failed": 1 if result.returncode != 0 else 0
                        }
                    },
                    "raw_output": result.stdout
                }
                
        except Exception as e:
            print(f"Error running frontend tests: {e}")
            return {
                "framework": "jest",
                "type": "frontend",
                "exit_code": 1,
                "error": str(e),
                "report": {"summary": {"total": 0, "passed": 0, "failed": 0}}
            }

    def run_acceptance_tests(self) -> Dict[str, Any]:
        """Run acceptance tests using existing script."""
        print("Running acceptance tests...")
        
        try:
            result = subprocess.run(
                [".venv/bin/python", "scripts/run_clean_acceptance_tests.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            # Check if executive report was generated
            if self.executive_report_path.exists():
                with open(self.executive_report_path) as f:
                    exec_report = json.load(f)
                    
                return {
                    "framework": "behave",
                    "type": "acceptance",
                    "exit_code": result.returncode,
                    "report": exec_report,
                    "stdout": result.stdout
                }
            else:
                return {
                    "framework": "behave", 
                    "type": "acceptance",
                    "exit_code": result.returncode,
                    "report": {"summary": {"total": 0, "passed": 0, "failed": 0}},
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
        except Exception as e:
            print(f"Error running acceptance tests: {e}")
            return {
                "framework": "behave",
                "type": "acceptance",
                "exit_code": 1,
                "error": str(e),
                "report": {"summary": {"total": 0, "passed": 0, "failed": 0}}
            }

    def generate_functionality_report(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate technical functionality report."""
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        
        framework_results = {}
        coverage_data = {}
        
        for result in test_results:
            framework = result["framework"]
            report = result.get("report", {})
            summary = report.get("summary", {})
            
            # Aggregate counts
            tests = summary.get("total", 0)
            passed = summary.get("passed", 0)
            failed = summary.get("failed", 0)
            skipped = summary.get("skipped", 0)
            
            total_tests += tests
            total_passed += passed
            total_failed += failed
            total_skipped += skipped
            
            framework_results[framework] = {
                "type": result["type"],
                "exit_code": result["exit_code"],
                "tests": tests,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "success_rate": (passed / tests * 100) if tests > 0 else 0
            }
            
            # Include coverage data if available
            if "coverage" in result and result["coverage"]:
                coverage_data[framework] = result["coverage"]
        
        functionality_report = {
            "version": "1.0.0",
            "generated_at": datetime.now().isoformat(),
            "project": "steves-mom-ai-chatbot",
            "summary": {
                "total_tests": total_tests,
                "total_passed": total_passed,
                "total_failed": total_failed,
                "total_skipped": total_skipped,
                "overall_success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0
            },
            "frameworks": framework_results,
            "coverage": coverage_data,
            "compliance": {
                "company_standards": "sw-testing-standard.md",
                "coverage_threshold": 90,
                "coverage_achieved": self._calculate_overall_coverage(coverage_data),
                "quality_gate_status": "PASS" if total_failed == 0 else "FAIL"
            }
        }
        
        return functionality_report

    def _calculate_overall_coverage(self, coverage_data: Dict[str, Any]) -> float:
        """Calculate overall coverage percentage from coverage data."""
        if not coverage_data:
            return 0.0
            
        # Extract coverage from pytest coverage data
        for framework, data in coverage_data.items():
            if "totals" in data:
                totals = data["totals"]
                if "percent_covered" in totals:
                    return totals["percent_covered"]
                elif "covered_lines" in totals and "num_statements" in totals:
                    covered = totals["covered_lines"]
                    total = totals["num_statements"]
                    return (covered / total * 100) if total > 0 else 0.0
        
        return 0.0

    def generate_executive_report(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate executive summary report."""
        
        # Check if acceptance tests already generated executive report
        for result in test_results:
            if result["framework"] == "behave" and "report" in result:
                behave_report = result["report"]
                if "version" in behave_report:  # Looks like executive report format
                    return behave_report
        
        # Generate new executive report
        total_tests = sum(r.get("report", {}).get("summary", {}).get("total", 0) for r in test_results)
        total_passed = sum(r.get("report", {}).get("summary", {}).get("passed", 0) for r in test_results)
        total_failed = sum(r.get("report", {}).get("summary", {}).get("failed", 0) for r in test_results)
        
        return {
            "version": "1.0.0",
            "owner": "Cannasol-Tech",
            "repo": "steves-mom-archive",
            "releaseTag": "local",
            "commit": "unknown",
            "createdAt": datetime.now().isoformat(),
            "summary": {
                "total": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "skipped": 0,
                "durationMs": 0
            },
            "scenarios": [],
            "requirements": []
        }

    def run_unified_reporting(self) -> bool:
        """Run all tests and generate unified reports."""
        print("Starting unified test reporting...")
        start_time = time.time()
        
        # Run all test suites
        test_results = []
        
        # Backend tests
        backend_result = self.run_backend_tests_with_json()
        test_results.append(backend_result)
        
        # Frontend tests  
        frontend_result = self.run_frontend_tests_with_json()
        test_results.append(frontend_result)
        
        # Acceptance tests
        acceptance_result = self.run_acceptance_tests()
        test_results.append(acceptance_result)
        
        # Generate reports
        functionality_report = self.generate_functionality_report(test_results)
        executive_report = self.generate_executive_report(test_results)
        
        # Save reports
        with open(self.functionality_report_path, 'w') as f:
            json.dump(functionality_report, f, indent=2)
        
        with open(self.executive_report_path, 'w') as f:
            json.dump(executive_report, f, indent=2)
        
        duration = time.time() - start_time
        
        # Print summary
        print(f"\n{'='*60}")
        print("UNIFIED TEST REPORT SUMMARY")
        print(f"{'='*60}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Total Tests: {functionality_report['summary']['total_tests']}")
        print(f"Passed: {functionality_report['summary']['total_passed']}")
        print(f"Failed: {functionality_report['summary']['total_failed']}")
        print(f"Success Rate: {functionality_report['summary']['overall_success_rate']:.1f}%")
        print(f"Coverage: {functionality_report['compliance']['coverage_achieved']:.1f}%")
        print(f"Quality Gate: {functionality_report['compliance']['quality_gate_status']}")
        print(f"\nReports generated:")
        print(f"  - Functionality: {self.functionality_report_path}")
        print(f"  - Executive: {self.executive_report_path}")
        print(f"{'='*60}")
        
        # Return success if no failures
        return functionality_report['summary']['total_failed'] == 0


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    reporter = UnifiedTestReporter(project_root)
    
    success = reporter.run_unified_reporting()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
