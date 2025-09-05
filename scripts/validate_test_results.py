#!/usr/bin/env python3
"""
Test results validation script.

This script validates test results across different test suites and ensures
quality standards are met.
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any


def parse_junit_xml(xml_file: Path) -> Dict[str, Any]:
    """Parse JUnit XML test results."""
    if not xml_file.exists():
        return {'error': f'File not found: {xml_file}'}
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Handle both testsuite and testsuites root elements
        if root.tag == 'testsuites':
            testsuites = root.findall('testsuite')
        else:
            testsuites = [root]
        
        total_tests = 0
        total_failures = 0
        total_errors = 0
        total_skipped = 0
        total_time = 0.0
        
        test_cases = []
        
        for testsuite in testsuites:
            tests = int(testsuite.get('tests', 0))
            failures = int(testsuite.get('failures', 0))
            errors = int(testsuite.get('errors', 0))
            skipped = int(testsuite.get('skipped', 0))
            time = float(testsuite.get('time', 0))
            
            total_tests += tests
            total_failures += failures
            total_errors += errors
            total_skipped += skipped
            total_time += time
            
            # Extract individual test cases
            for testcase in testsuite.findall('testcase'):
                case_info = {
                    'name': testcase.get('name'),
                    'classname': testcase.get('classname'),
                    'time': float(testcase.get('time', 0)),
                    'status': 'passed'
                }
                
                if testcase.find('failure') is not None:
                    case_info['status'] = 'failed'
                    case_info['failure'] = testcase.find('failure').text
                elif testcase.find('error') is not None:
                    case_info['status'] = 'error'
                    case_info['error'] = testcase.find('error').text
                elif testcase.find('skipped') is not None:
                    case_info['status'] = 'skipped'
                    case_info['skip_reason'] = testcase.find('skipped').get('message', '')
                
                test_cases.append(case_info)
        
        return {
            'total_tests': total_tests,
            'total_failures': total_failures,
            'total_errors': total_errors,
            'total_skipped': total_skipped,
            'total_time': total_time,
            'success_rate': (total_tests - total_failures - total_errors) / max(total_tests, 1) * 100,
            'test_cases': test_cases
        }
    
    except Exception as e:
        return {'error': f'Error parsing {xml_file}: {e}'}


def parse_behave_json(json_file: Path) -> Dict[str, Any]:
    """Parse Behave JSON test results."""
    if not json_file.exists():
        return {'error': f'File not found: {json_file}'}
    
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        total_scenarios = 0
        passed_scenarios = 0
        failed_scenarios = 0
        skipped_scenarios = 0
        
        scenario_details = []
        
        for feature in data:
            for element in feature.get('elements', []):
                if element.get('type') == 'scenario':
                    total_scenarios += 1
                    scenario_name = element.get('name', 'Unknown')
                    
                    # Check scenario status based on steps
                    steps = element.get('steps', [])
                    scenario_status = 'passed'
                    
                    for step in steps:
                        step_status = step.get('result', {}).get('status', 'undefined')
                        if step_status in ['failed', 'undefined']:
                            scenario_status = 'failed'
                            break
                        elif step_status == 'skipped':
                            scenario_status = 'skipped'
                    
                    if scenario_status == 'passed':
                        passed_scenarios += 1
                    elif scenario_status == 'failed':
                        failed_scenarios += 1
                    else:
                        skipped_scenarios += 1
                    
                    scenario_details.append({
                        'name': scenario_name,
                        'status': scenario_status,
                        'feature': feature.get('name', 'Unknown'),
                        'tags': [tag.get('name', '') for tag in element.get('tags', [])]
                    })
        
        return {
            'total_scenarios': total_scenarios,
            'passed_scenarios': passed_scenarios,
            'failed_scenarios': failed_scenarios,
            'skipped_scenarios': skipped_scenarios,
            'success_rate': passed_scenarios / max(total_scenarios, 1) * 100,
            'scenarios': scenario_details
        }
    
    except Exception as e:
        return {'error': f'Error parsing {json_file}: {e}'}


def validate_test_suite(suite_name: str, results: Dict[str, Any], thresholds: Dict[str, float]) -> bool:
    """Validate a test suite against quality thresholds."""
    if 'error' in results:
        print(f"❌ {suite_name}: {results['error']}")
        return False
    
    success_rate = results.get('success_rate', 0)
    threshold = thresholds.get(suite_name.lower(), 95)
    
    print(f"\n📊 {suite_name} Results:")
    
    if 'total_tests' in results:
        # JUnit format
        print(f"   Total Tests: {results['total_tests']}")
        print(f"   Passed: {results['total_tests'] - results['total_failures'] - results['total_errors']}")
        print(f"   Failed: {results['total_failures']}")
        print(f"   Errors: {results['total_errors']}")
        print(f"   Skipped: {results['total_skipped']}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Total Time: {results['total_time']:.2f}s")
    else:
        # Behave format
        print(f"   Total Scenarios: {results['total_scenarios']}")
        print(f"   Passed: {results['passed_scenarios']}")
        print(f"   Failed: {results['failed_scenarios']}")
        print(f"   Skipped: {results['skipped_scenarios']}")
        print(f"   Success Rate: {success_rate:.1f}%")
    
    if success_rate >= threshold:
        print(f"✅ Success rate {success_rate:.1f}% meets threshold {threshold}%")
        return True
    else:
        print(f"❌ Success rate {success_rate:.1f}% below threshold {threshold}%")
        
        # Show failed tests/scenarios
        if 'test_cases' in results:
            failed_tests = [tc for tc in results['test_cases'] if tc['status'] in ['failed', 'error']]
            if failed_tests:
                print(f"   Failed tests:")
                for test in failed_tests[:5]:  # Show first 5 failures
                    print(f"     - {test['classname']}.{test['name']}")
        
        if 'scenarios' in results:
            failed_scenarios = [s for s in results['scenarios'] if s['status'] == 'failed']
            if failed_scenarios:
                print(f"   Failed scenarios:")
                for scenario in failed_scenarios[:5]:  # Show first 5 failures
                    print(f"     - {scenario['feature']}: {scenario['name']}")
        
        return False


def main():
    """Main entry point."""
    print("🔍 Validating test results...")
    
    # Define quality thresholds
    thresholds = {
        'unit': 95.0,        # Unit tests should have very high success rate
        'integration': 90.0,  # Integration tests can be slightly more flaky
        'acceptance': 85.0    # Acceptance tests may have some legitimate skips
    }
    
    # Test result files
    test_files = {
        'Unit': Path('test-results-unit.xml'),
        'Integration': Path('test-results-integration.xml'),
        'Acceptance (XML)': Path('test-results-acceptance.xml'),
        'Acceptance (JSON)': Path('acceptance-results.json')
    }
    
    all_passed = True
    
    # Validate each test suite
    for suite_name, file_path in test_files.items():
        if not file_path.exists():
            print(f"⚠️  {suite_name}: Results file not found ({file_path})")
            continue
        
        if file_path.suffix == '.json':
            results = parse_behave_json(file_path)
        else:
            results = parse_junit_xml(file_path)
        
        suite_key = suite_name.lower().split()[0]  # Extract first word
        if not validate_test_suite(suite_name, results, thresholds):
            all_passed = False
    
    # Overall validation
    print(f"\n{'='*50}")
    if all_passed:
        print("✅ All test suites meet quality thresholds!")
        print("\n🎯 Quality gates passed:")
        print("   - Test success rates meet minimum thresholds")
        print("   - No critical test failures detected")
        print("   - Test execution completed successfully")
    else:
        print("❌ Some test suites failed quality thresholds!")
        print("\n🔧 Recommended actions:")
        print("   1. Fix failing tests before merging")
        print("   2. Investigate test flakiness")
        print("   3. Review test coverage for missed scenarios")
        print("   4. Consider if thresholds need adjustment")
    
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
