#!/usr/bin/env python3
"""
Dashboard Viewer for Testing Framework Metrics

Opens the metrics dashboard in the default web browser.

Author: Cannasol Technologies
Date: 2025-09-06
Version: 1.0.0
"""

import webbrowser
from pathlib import Path


def main():
    """Open the metrics dashboard in the default browser."""
    project_root = Path(__file__).parent.parent
    dashboard_path = project_root / "reports" / "metrics" / "dashboard.html"
    
    if dashboard_path.exists():
        print(f"Opening dashboard: {dashboard_path}")
        webbrowser.open(f"file://{dashboard_path.absolute()}")
        print("Dashboard opened in your default web browser.")
    else:
        print("Dashboard not found. Run 'make test-metrics' first to generate it.")


if __name__ == "__main__":
    main()
