#!/usr/bin/env python3
"""
Clean test output formatter for acceptance tests.

This script provides clean, colorized output for acceptance test results
with clear visual hierarchy and easy-to-scan information.
"""
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional


class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Colors
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Background colors
    BG_GREEN = '\033[42m'
    BG_RED = '\033[41m'
    BG_YELLOW = '\033[43m'
    
    # Bright colors
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_CYAN = '\033[96m'


class TestOutputFormatter:
    """Formats test output in a clean, professional manner."""
    
    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors and sys.stdout.isatty()
        self.c = Colors() if self.use_colors else type('', (), {k: '' for k in dir(Colors) if not k.startswith('_')})()
    
    def print_header(self, title: str, emoji: str = "🧪"):
        """Print a formatted header."""
        print(f"\n{self.c.BOLD}{self.c.BRIGHT_CYAN}{emoji} {title}{self.c.RESET}")
        print(f"{self.c.DIM}{'━' * (len(title) + 3)}{self.c.RESET}")
    
    def print_step(self, message: str, emoji: str = "⚡"):
        """Print a step message."""
        print(f"{self.c.DIM}{emoji} {message}...{self.c.RESET}")
    
    def print_success(self, message: str, emoji: str = "✅"):
        """Print a success message."""
        print(f"{self.c.BRIGHT_GREEN}{emoji} {message}{self.c.RESET}")
    
    def print_warning(self, message: str, emoji: str = "⚠️"):
        """Print a warning message."""
        print(f"{self.c.BRIGHT_YELLOW}{emoji} {message}{self.c.RESET}")
    
    def print_error(self, message: str, emoji: str = "❌"):
        """Print an error message."""
        print(f"{self.c.BRIGHT_RED}{emoji} {message}{self.c.RESET}")
    
    def print_info(self, message: str, emoji: str = "ℹ️"):
        """Print an info message."""
        print(f"{self.c.BRIGHT_BLUE}{emoji} {message}{self.c.RESET}")
    
    def print_summary_box(self, title: str, content: Dict[str, Any]):
        """Print a formatted summary box."""
        print(f"\n{self.c.BOLD}{self.c.BRIGHT_CYAN}📊 {title}{self.c.RESET}")
        print(f"{self.c.DIM}{'━' * 50}{self.c.RESET}")
        
        for key, value in content.items():
            if isinstance(value, bool):
                icon = "✅" if value else "❌"
                color = self.c.BRIGHT_GREEN if value else self.c.BRIGHT_RED
            elif isinstance(value, (int, float)) and key.lower().endswith(('time', 'duration')):
                icon = "⏱️"
                color = self.c.BRIGHT_BLUE
                if isinstance(value, float):
                    value = f"{value:.1f}s"
            else:
                icon = "📋"
                color = self.c.WHITE
            
            print(f"{color}{icon} {key}: {value}{self.c.RESET}")
    
    def format_behave_results(self, behave_output: str) -> Dict[str, Any]:
        """Parse and format behave output."""
        lines = behave_output.strip().split('\n')
        
        # Find the summary lines
        summary_line = None
        scenario_line = None
        steps_line = None
        time_line = None
        
        for line in lines:
            if 'features passed' in line:
                summary_line = line
            elif 'scenarios passed' in line:
                scenario_line = line
            elif 'steps passed' in line:
                steps_line = line
            elif 'Took' in line:
                time_line = line
        
        # Parse the results
        results = {}
        
        if summary_line:
            # Parse "11 features passed, 0 failed, 0 skipped"
            import re
            numbers = re.findall(r'\d+', summary_line)
            if len(numbers) >= 3:
                features_passed, features_failed, features_skipped = map(int, numbers[:3])
                results['Features'] = f"{features_passed} passed, {features_failed} failed, {features_skipped} skipped"

        if scenario_line:
            # Parse "30 scenarios passed, 0 failed, 0 skipped"
            import re
            numbers = re.findall(r'\d+', scenario_line)
            if len(numbers) >= 3:
                scenarios_passed, scenarios_failed, scenarios_skipped = map(int, numbers[:3])
                results['Scenarios'] = f"{scenarios_passed} passed, {scenarios_failed} failed, {scenarios_skipped} skipped"

        if steps_line:
            # Parse "105 steps passed, 0 failed, 0 skipped, 0 undefined"
            import re
            numbers = re.findall(r'\d+', steps_line)
            if len(numbers) >= 3:
                steps_passed, steps_failed, steps_skipped = map(int, numbers[:3])
                results['Steps'] = f"{steps_passed} passed, {steps_failed} failed, {steps_skipped} skipped"
        
        if time_line:
            # Extract time from "Took 0m7.587s"
            time_part = time_line.split('Took ')[1] if 'Took ' in time_line else "0s"
            results['Duration'] = time_part
        
        return results
    
    def format_executive_report(self, report_path: Path) -> Optional[Dict[str, Any]]:
        """Format executive report information."""
        if not report_path.exists():
            return None
        
        try:
            with open(report_path, 'r') as f:
                data = json.load(f)
            
            summary = data.get('summary', {})
            return {
                'Total Tests': summary.get('total', 0),
                'Passed': summary.get('passed', 0),
                'Failed': summary.get('failed', 0),
                'Skipped': summary.get('skipped', 0),
                'Success Rate': f"{(summary.get('passed', 0) / max(summary.get('total', 1), 1) * 100):.1f}%",
                'Report Location': str(report_path)
            }
        except Exception:
            return None


def main():
    """Main entry point for clean test output formatting."""
    formatter = TestOutputFormatter()
    
    # Check if we're being called with behave output
    if len(sys.argv) > 1:
        behave_output = sys.argv[1]
        
        # Format the behave results
        results = formatter.format_behave_results(behave_output)
        
        # Print clean summary
        formatter.print_summary_box("Test Results Summary", results)
        
        # Check for executive report
        exec_report_path = Path("final/executive-report.json")
        exec_results = formatter.format_executive_report(exec_report_path)
        
        if exec_results:
            formatter.print_summary_box("Executive Report", exec_results)
        
        # Print completion message
        all_passed = 'failed, 0' in behave_output and 'skipped, 0' in behave_output
        if all_passed:
            formatter.print_success("All acceptance tests passed! 🎉")
        else:
            formatter.print_warning("Some tests need attention")
    
    else:
        # Default usage message
        formatter.print_header("Clean Test Output Formatter")
        formatter.print_info("Usage: python scripts/clean_test_output.py '<behave_output>'")


if __name__ == '__main__':
    main()
