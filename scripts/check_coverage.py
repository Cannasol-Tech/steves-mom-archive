#!/usr/bin/env python3
"""
Coverage threshold enforcement script.

This script checks test coverage against defined thresholds and fails
the build if coverage is below acceptable levels.
"""
import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_coverage_xml(coverage_file: Path) -> dict:
    """Parse coverage.xml file and extract coverage metrics."""
    if not coverage_file.exists():
        print(f"❌ Coverage file not found: {coverage_file}")
        return {}
    
    try:
        tree = ET.parse(coverage_file)
        root = tree.getroot()
        
        # Extract overall coverage
        coverage_elem = root.find('.//coverage')
        if coverage_elem is not None:
            line_rate = float(coverage_elem.get('line-rate', 0)) * 100
            branch_rate = float(coverage_elem.get('branch-rate', 0)) * 100
        else:
            line_rate = 0
            branch_rate = 0
        
        # Extract package-level coverage
        packages = {}
        for package in root.findall('.//package'):
            name = package.get('name', 'unknown')
            pkg_line_rate = float(package.get('line-rate', 0)) * 100
            pkg_branch_rate = float(package.get('branch-rate', 0)) * 100
            packages[name] = {
                'line_coverage': pkg_line_rate,
                'branch_coverage': pkg_branch_rate
            }
        
        return {
            'overall_line_coverage': line_rate,
            'overall_branch_coverage': branch_rate,
            'packages': packages
        }
    
    except Exception as e:
        print(f"❌ Error parsing coverage file: {e}")
        return {}


def check_coverage_thresholds(coverage_data: dict, thresholds: dict) -> bool:
    """Check if coverage meets defined thresholds."""
    if not coverage_data:
        print("❌ No coverage data available")
        return False
    
    overall_line = coverage_data.get('overall_line_coverage', 0)
    overall_branch = coverage_data.get('overall_branch_coverage', 0)
    
    print(f"📊 Coverage Report:")
    print(f"   Overall Line Coverage: {overall_line:.1f}%")
    print(f"   Overall Branch Coverage: {overall_branch:.1f}%")
    
    # Check overall thresholds
    line_threshold = thresholds.get('line_coverage', 80)
    branch_threshold = thresholds.get('branch_coverage', 70)
    
    line_pass = overall_line >= line_threshold
    branch_pass = overall_branch >= branch_threshold
    
    if line_pass:
        print(f"✅ Line coverage {overall_line:.1f}% meets threshold {line_threshold}%")
    else:
        print(f"❌ Line coverage {overall_line:.1f}% below threshold {line_threshold}%")
    
    if branch_pass:
        print(f"✅ Branch coverage {overall_branch:.1f}% meets threshold {branch_threshold}%")
    else:
        print(f"❌ Branch coverage {overall_branch:.1f}% below threshold {branch_threshold}%")
    
    # Check package-specific thresholds
    package_thresholds = thresholds.get('packages', {})
    package_failures = []
    
    for package_name, package_data in coverage_data.get('packages', {}).items():
        if package_name in package_thresholds:
            pkg_threshold = package_thresholds[package_name]
            pkg_line = package_data['line_coverage']
            
            if pkg_line < pkg_threshold:
                package_failures.append(f"{package_name}: {pkg_line:.1f}% < {pkg_threshold}%")
                print(f"❌ Package {package_name} coverage {pkg_line:.1f}% below threshold {pkg_threshold}%")
            else:
                print(f"✅ Package {package_name} coverage {pkg_line:.1f}% meets threshold {pkg_threshold}%")
    
    if package_failures:
        print(f"\n❌ Package coverage failures:")
        for failure in package_failures:
            print(f"   {failure}")
    
    return line_pass and branch_pass and not package_failures


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Check test coverage thresholds')
    parser.add_argument('--threshold', type=float, default=80,
                       help='Overall line coverage threshold (default: 80)')
    parser.add_argument('--branch-threshold', type=float, default=70,
                       help='Branch coverage threshold (default: 70)')
    parser.add_argument('--coverage-file', type=Path, default=Path('coverage.xml'),
                       help='Path to coverage.xml file')
    parser.add_argument('--config', type=Path,
                       help='Path to coverage configuration file')
    
    args = parser.parse_args()
    
    # Define thresholds
    thresholds = {
        'line_coverage': args.threshold,
        'branch_coverage': args.branch_threshold,
        'packages': {
            'backend.ai': 85,  # AI components should have high coverage
            'backend.api': 90,  # API routes should be well tested
            'backend.models': 80,  # Data models coverage
            'backend.services': 85,  # Business logic coverage
        }
    }
    
    # Parse coverage data
    coverage_data = parse_coverage_xml(args.coverage_file)
    
    # Check thresholds
    if check_coverage_thresholds(coverage_data, thresholds):
        print("\n✅ All coverage thresholds met!")
        sys.exit(0)
    else:
        print("\n❌ Coverage thresholds not met!")
        print("\nTo improve coverage:")
        print("1. Add unit tests for uncovered code")
        print("2. Review and test edge cases")
        print("3. Add integration tests for complex workflows")
        print("4. Consider if some code should be excluded from coverage")
        sys.exit(1)


if __name__ == '__main__':
    main()
