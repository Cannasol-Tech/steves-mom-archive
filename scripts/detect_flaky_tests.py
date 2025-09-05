#!/usr/bin/env python3
"""
Flaky test detection script.

This script analyzes test results over time to identify flaky tests that
pass/fail inconsistently and may need attention.
"""
import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Any, Tuple
import argparse


class FlakyTestDetector:
    """Detects flaky tests based on historical test results."""
    
    def __init__(self, history_file: Path = Path('test-history.json')):
        self.history_file = history_file
        self.test_history = self.load_history()
    
    def load_history(self) -> Dict[str, List[str]]:
        """Load test execution history from file."""
        if not self.history_file.exists():
            return {}
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Warning: Could not load test history: {e}")
            return {}
    
    def save_history(self):
        """Save test execution history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.test_history, f, indent=2)
        except Exception as e:
            print(f"⚠️  Warning: Could not save test history: {e}")
    
    def add_test_results(self, test_results: List[Dict[str, Any]]):
        """Add new test results to history."""
        for test in test_results:
            test_id = f"{test.get('classname', '')}.{test.get('name', '')}"
            status = test.get('status', 'unknown')
            
            if test_id not in self.test_history:
                self.test_history[test_id] = []
            
            # Keep only last 20 results to prevent unbounded growth
            self.test_history[test_id].append(status)
            if len(self.test_history[test_id]) > 20:
                self.test_history[test_id] = self.test_history[test_id][-20:]
    
    def detect_flaky_tests(self, min_runs: int = 5, flaky_threshold: float = 0.2) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Detect flaky tests based on inconsistent results.
        
        Args:
            min_runs: Minimum number of test runs to consider
            flaky_threshold: Minimum failure rate to consider flaky (0.0-1.0)
        
        Returns:
            List of (test_id, flaky_stats) tuples
        """
        flaky_tests = []
        
        for test_id, results in self.test_history.items():
            if len(results) < min_runs:
                continue
            
            # Count different outcomes
            status_counts = Counter(results)
            total_runs = len(results)
            
            # Calculate failure rate (failed + error)
            failures = status_counts.get('failed', 0) + status_counts.get('error', 0)
            failure_rate = failures / total_runs
            
            # Calculate inconsistency (how often status changes)
            changes = sum(1 for i in range(1, len(results)) if results[i] != results[i-1])
            inconsistency_rate = changes / max(total_runs - 1, 1)
            
            # Detect flakiness
            is_flaky = (
                failure_rate > flaky_threshold and 
                failure_rate < (1 - flaky_threshold) and
                inconsistency_rate > 0.3
            )
            
            if is_flaky:
                flaky_stats = {
                    'total_runs': total_runs,
                    'failure_rate': failure_rate,
                    'inconsistency_rate': inconsistency_rate,
                    'status_counts': dict(status_counts),
                    'recent_results': results[-10:],  # Last 10 results
                    'pattern': self.analyze_pattern(results)
                }
                flaky_tests.append((test_id, flaky_stats))
        
        # Sort by inconsistency rate (most flaky first)
        flaky_tests.sort(key=lambda x: x[1]['inconsistency_rate'], reverse=True)
        return flaky_tests
    
    def analyze_pattern(self, results: List[str]) -> str:
        """Analyze the pattern of test results."""
        if len(results) < 3:
            return "insufficient_data"
        
        # Check for alternating pattern
        alternating = all(results[i] != results[i+1] for i in range(len(results)-1))
        if alternating:
            return "alternating"
        
        # Check for recent degradation
        recent_failures = sum(1 for r in results[-5:] if r in ['failed', 'error'])
        if recent_failures >= 3:
            return "recent_degradation"
        
        # Check for intermittent failures
        failure_positions = [i for i, r in enumerate(results) if r in ['failed', 'error']]
        if failure_positions:
            gaps = [failure_positions[i+1] - failure_positions[i] for i in range(len(failure_positions)-1)]
            if gaps and max(gaps) > 3:
                return "intermittent"
        
        return "inconsistent"
    
    def get_slow_tests(self, test_results: List[Dict[str, Any]], threshold: float = 10.0) -> List[Tuple[str, float]]:
        """Identify slow tests that may need optimization."""
        slow_tests = []
        
        for test in test_results:
            test_id = f"{test.get('classname', '')}.{test.get('name', '')}"
            time = test.get('time', 0)
            
            if time > threshold:
                slow_tests.append((test_id, time))
        
        slow_tests.sort(key=lambda x: x[1], reverse=True)
        return slow_tests


def parse_test_results(xml_file: Path) -> List[Dict[str, Any]]:
    """Parse test results from JUnit XML."""
    if not xml_file.exists():
        return []
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        test_cases = []
        
        # Handle both testsuite and testsuites root elements
        if root.tag == 'testsuites':
            testsuites = root.findall('testsuite')
        else:
            testsuites = [root]
        
        for testsuite in testsuites:
            for testcase in testsuite.findall('testcase'):
                case_info = {
                    'name': testcase.get('name'),
                    'classname': testcase.get('classname'),
                    'time': float(testcase.get('time', 0)),
                    'status': 'passed'
                }
                
                if testcase.find('failure') is not None:
                    case_info['status'] = 'failed'
                elif testcase.find('error') is not None:
                    case_info['status'] = 'error'
                elif testcase.find('skipped') is not None:
                    case_info['status'] = 'skipped'
                
                test_cases.append(case_info)
        
        return test_cases
    
    except Exception as e:
        print(f"❌ Error parsing {xml_file}: {e}")
        return []


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Detect flaky and slow tests')
    parser.add_argument('--min-runs', type=int, default=5,
                       help='Minimum test runs to consider for flakiness (default: 5)')
    parser.add_argument('--flaky-threshold', type=float, default=0.2,
                       help='Minimum failure rate to consider flaky (default: 0.2)')
    parser.add_argument('--slow-threshold', type=float, default=10.0,
                       help='Time threshold for slow tests in seconds (default: 10.0)')
    parser.add_argument('--history-file', type=Path, default=Path('test-history.json'),
                       help='Path to test history file')
    
    args = parser.parse_args()
    
    print("🔍 Analyzing test results for flakiness and performance issues...")
    
    # Initialize detector
    detector = FlakyTestDetector(args.history_file)
    
    # Parse current test results
    test_files = [
        Path('test-results-unit.xml'),
        Path('test-results-integration.xml')
    ]
    
    all_test_results = []
    for test_file in test_files:
        if test_file.exists():
            results = parse_test_results(test_file)
            all_test_results.extend(results)
            print(f"📊 Loaded {len(results)} test results from {test_file}")
    
    if not all_test_results:
        print("⚠️  No test results found to analyze")
        return
    
    # Add results to history
    detector.add_test_results(all_test_results)
    detector.save_history()
    
    # Detect flaky tests
    flaky_tests = detector.detect_flaky_tests(args.min_runs, args.flaky_threshold)
    
    if flaky_tests:
        print(f"\n🔥 Found {len(flaky_tests)} potentially flaky tests:")
        for test_id, stats in flaky_tests[:10]:  # Show top 10
            print(f"\n   📍 {test_id}")
            print(f"      Failure rate: {stats['failure_rate']:.1%}")
            print(f"      Inconsistency: {stats['inconsistency_rate']:.1%}")
            print(f"      Pattern: {stats['pattern']}")
            print(f"      Recent: {' → '.join(stats['recent_results'])}")
    else:
        print("\n✅ No flaky tests detected")
    
    # Detect slow tests
    slow_tests = detector.get_slow_tests(all_test_results, args.slow_threshold)
    
    if slow_tests:
        print(f"\n🐌 Found {len(slow_tests)} slow tests (>{args.slow_threshold}s):")
        for test_id, time in slow_tests[:10]:  # Show top 10
            print(f"   📍 {test_id}: {time:.2f}s")
    else:
        print(f"\n✅ No slow tests detected (threshold: {args.slow_threshold}s)")
    
    # Summary and recommendations
    print(f"\n{'='*50}")
    if flaky_tests or slow_tests:
        print("🔧 Recommendations:")
        if flaky_tests:
            print("   1. Investigate flaky tests for timing issues or dependencies")
            print("   2. Add proper setup/teardown and isolation")
            print("   3. Consider quarantining consistently flaky tests")
        if slow_tests:
            print("   4. Optimize slow tests or mark them with @pytest.mark.slow")
            print("   5. Consider parallelization for test suites")
        
        # Exit with warning code if flaky tests found
        sys.exit(1 if flaky_tests else 0)
    else:
        print("✅ Test suite health looks good!")
        print("   - No flaky tests detected")
        print("   - No slow tests found")
        sys.exit(0)


if __name__ == '__main__':
    main()
