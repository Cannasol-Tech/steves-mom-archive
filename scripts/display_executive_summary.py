#!/usr/bin/env python3
"""
Executive summary display for acceptance test results.

This script provides a comprehensive, dashboard-style view of test results,
PRD requirement coverage, and key metrics.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.clean_test_output import TestOutputFormatter, Colors


class ExecutiveSummaryDisplay:
    """Displays executive summary in a dashboard-style format."""
    
    def __init__(self, use_colors: bool = True):
        self.formatter = TestOutputFormatter(use_colors)
        self.c = Colors() if use_colors and sys.stdout.isatty() else type('', (), {k: '' for k in dir(Colors) if not k.startswith('_')})()
    
    def load_executive_report(self, report_path: Path) -> Optional[Dict[str, Any]]:
        """Load and validate executive report."""
        if not report_path.exists():
            return None
        
        try:
            with open(report_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.formatter.print_error(f"Failed to load executive report: {e}")
            return None
    
    def display_test_overview(self, report: Dict[str, Any]):
        """Display high-level test overview."""
        summary = report.get('summary', {})
        
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        skipped = summary.get('skipped', 0)
        duration_ms = summary.get('durationMs', 0)
        
        success_rate = (passed / max(total, 1)) * 100
        duration_s = duration_ms / 1000 if duration_ms > 0 else 0
        
        # Overall status
        if failed == 0 and total > 0:
            status_icon = "✅"
            status_text = "PASSING"
            status_color = self.c.BRIGHT_GREEN
        elif failed > 0:
            status_icon = "❌"
            status_text = "FAILING"
            status_color = self.c.BRIGHT_RED
        else:
            status_icon = "⚠️"
            status_text = "NO TESTS"
            status_color = self.c.BRIGHT_YELLOW
        
        print(f"\n{self.c.BOLD}{self.c.BRIGHT_CYAN}📊 Test Suite Overview{self.c.RESET}")
        print(f"{self.c.DIM}{'━' * 50}{self.c.RESET}")
        
        print(f"{status_color}{status_icon} Status: {status_text}{self.c.RESET}")
        print(f"{self.c.BRIGHT_BLUE}📈 Success Rate: {success_rate:.1f}%{self.c.RESET}")
        print(f"{self.c.WHITE}📋 Total Scenarios: {total}{self.c.RESET}")
        print(f"{self.c.BRIGHT_GREEN}✅ Passed: {passed}{self.c.RESET}")
        
        if failed > 0:
            print(f"{self.c.BRIGHT_RED}❌ Failed: {failed}{self.c.RESET}")
        
        if skipped > 0:
            print(f"{self.c.BRIGHT_YELLOW}⏭️  Skipped: {skipped}{self.c.RESET}")
        
        if duration_s > 0:
            print(f"{self.c.BRIGHT_BLUE}⏱️  Duration: {duration_s:.1f}s{self.c.RESET}")
    
    def display_requirement_coverage(self, report: Dict[str, Any]):
        """Display PRD requirement coverage."""
        requirements = report.get('requirements', [])
        
        if not requirements:
            return
        
        print(f"\n{self.c.BOLD}{self.c.BRIGHT_CYAN}🎯 PRD Requirement Coverage{self.c.RESET}")
        print(f"{self.c.DIM}{'━' * 50}{self.c.RESET}")
        
        # Group requirements by category based on ID prefix
        req_categories = {}
        for req in requirements:
            req_id = req.get('id', '')

            # Categorize based on ID prefix
            if req_id.startswith('FR-1'):
                category = 'Core Chat Interface (FR-1.x)'
            elif req_id.startswith('FR-2'):
                category = 'Task Generation & Workflow (FR-2.x)'
            elif req_id.startswith('FR-3'):
                category = 'System Integrations (FR-3.x)'
            elif req_id.startswith('FR-4'):
                category = 'Security & Access Control (FR-4.x)'
            elif req_id.startswith('FR-5'):
                category = 'Analytics & Learning (FR-5.x)'
            elif req_id.startswith('NFR-1'):
                category = 'Performance & Scalability (NFR-1.x)'
            elif req_id.startswith('NFR-2'):
                category = 'Security Requirements (NFR-2.x)'
            elif req_id.startswith('NFR-3'):
                category = 'Reliability Requirements (NFR-3.x)'
            elif req_id.startswith('NFR-4'):
                category = 'Usability Requirements (NFR-4.x)'
            elif req_id.startswith('PRD-'):
                category = 'Product Requirements (PRD)'
            else:
                category = 'Other'

            if category not in req_categories:
                req_categories[category] = []
            req_categories[category].append(req)
        
        for category, reqs in req_categories.items():
            total_reqs = len(reqs)

            # Calculate coverage based on scenario status
            covered_reqs = 0
            for req in reqs:
                scenarios = req.get('scenarios', [])
                if scenarios:  # If there are scenarios, it means the requirement is covered
                    covered_reqs += 1

            coverage_pct = (covered_reqs / max(total_reqs, 1)) * 100

            if coverage_pct == 100:
                icon = "✅"
                color = self.c.BRIGHT_GREEN
            elif coverage_pct >= 80:
                icon = "🟡"
                color = self.c.BRIGHT_YELLOW
            else:
                icon = "❌"
                color = self.c.BRIGHT_RED

            print(f"{color}{icon} {category}: {covered_reqs}/{total_reqs} ({coverage_pct:.0f}%){self.c.RESET}")
    
    def display_scenario_breakdown(self, report: Dict[str, Any]):
        """Display scenario breakdown by feature."""
        scenarios = report.get('scenarios', [])
        
        if not scenarios:
            return
        
        print(f"\n{self.c.BOLD}{self.c.BRIGHT_CYAN}🔍 Feature Breakdown{self.c.RESET}")
        print(f"{self.c.DIM}{'━' * 50}{self.c.RESET}")
        
        # Group scenarios by feature
        features = {}
        for scenario in scenarios:
            feature_name = scenario.get('feature', 'Unknown Feature')
            if feature_name not in features:
                features[feature_name] = {'passed': 0, 'failed': 0, 'skipped': 0}
            
            status = scenario.get('status', 'unknown')
            if status == 'passed':
                features[feature_name]['passed'] += 1
            elif status == 'failed':
                features[feature_name]['failed'] += 1
            else:
                features[feature_name]['skipped'] += 1
        
        for feature_name, counts in features.items():
            total = counts['passed'] + counts['failed'] + counts['skipped']
            
            if counts['failed'] == 0:
                icon = "✅"
                color = self.c.BRIGHT_GREEN
            else:
                icon = "❌"
                color = self.c.BRIGHT_RED
            
            print(f"{color}{icon} {feature_name}: {counts['passed']}/{total} passed{self.c.RESET}")
            
            if counts['failed'] > 0:
                print(f"   {self.c.BRIGHT_RED}└─ {counts['failed']} failed{self.c.RESET}")
            
            if counts['skipped'] > 0:
                print(f"   {self.c.BRIGHT_YELLOW}└─ {counts['skipped']} skipped{self.c.RESET}")
    
    def display_failed_scenarios(self, report: Dict[str, Any]):
        """Display details of failed scenarios."""
        scenarios = report.get('scenarios', [])
        failed_scenarios = [s for s in scenarios if s.get('status') == 'failed']
        
        if not failed_scenarios:
            return
        
        print(f"\n{self.c.BOLD}{self.c.BRIGHT_RED}🚨 Failed Scenarios{self.c.RESET}")
        print(f"{self.c.DIM}{'━' * 50}{self.c.RESET}")
        
        for scenario in failed_scenarios[:5]:  # Show first 5 failures
            name = scenario.get('name', 'Unknown Scenario')
            feature = scenario.get('feature', 'Unknown Feature')
            error = scenario.get('error', 'No error details available')
            
            print(f"{self.c.BRIGHT_RED}❌ {feature}: {name}{self.c.RESET}")
            print(f"   {self.c.DIM}└─ {error[:100]}{'...' if len(error) > 100 else ''}{self.c.RESET}")
        
        if len(failed_scenarios) > 5:
            remaining = len(failed_scenarios) - 5
            print(f"{self.c.DIM}... and {remaining} more failed scenarios{self.c.RESET}")
    
    def display_metadata(self, report: Dict[str, Any]):
        """Display report metadata."""
        print(f"\n{self.c.BOLD}{self.c.BRIGHT_CYAN}📋 Report Metadata{self.c.RESET}")
        print(f"{self.c.DIM}{'━' * 50}{self.c.RESET}")
        
        version = report.get('version', 'Unknown')
        owner = report.get('owner', 'Unknown')
        repo = report.get('repo', 'Unknown')
        release_tag = report.get('releaseTag', 'Unknown')
        commit = report.get('commit', 'Unknown')
        created_at = report.get('createdAt', 'Unknown')
        
        print(f"{self.c.WHITE}📦 Version: {version}{self.c.RESET}")
        print(f"{self.c.WHITE}🏢 Owner: {owner}{self.c.RESET}")
        print(f"{self.c.WHITE}📁 Repository: {repo}{self.c.RESET}")
        print(f"{self.c.WHITE}🏷️  Release: {release_tag}{self.c.RESET}")
        print(f"{self.c.WHITE}🔗 Commit: {commit[:8] if len(commit) > 8 else commit}{self.c.RESET}")
        
        if created_at and created_at != "":
            print(f"{self.c.WHITE}📅 Created: {created_at}{self.c.RESET}")
    
    def display_full_summary(self, report_path: Path):
        """Display complete executive summary."""
        report = self.load_executive_report(report_path)
        
        if not report:
            self.formatter.print_error(f"Could not load executive report from {report_path}")
            return
        
        # Header
        self.formatter.print_header("Executive Test Summary", "📊")
        
        # Main sections
        self.display_test_overview(report)
        self.display_requirement_coverage(report)
        self.display_scenario_breakdown(report)
        self.display_failed_scenarios(report)
        self.display_metadata(report)
        
        # Footer
        print(f"\n{self.c.DIM}{'━' * 50}{self.c.RESET}")
        self.formatter.print_info(f"Full report: {report_path}")


def main():
    """Main entry point."""
    display = ExecutiveSummaryDisplay()
    
    # Default report path
    report_path = Path("final/executive-report.json")
    
    # Allow custom path via command line
    if len(sys.argv) > 1:
        report_path = Path(sys.argv[1])
    
    display.display_full_summary(report_path)


if __name__ == '__main__':
    main()
