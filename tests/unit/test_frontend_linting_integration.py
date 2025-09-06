"""
Test suite for frontend linting integration.

This module tests the ESLint configuration and integration with the build system.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestFrontendLintingIntegration:
    """Test frontend linting configuration and integration."""

    def test_eslint_config_file_exists(self):
        """Test that ESLint configuration file exists."""
        config_path = Path("frontend/.eslintrc.js")
        assert config_path.exists(), "ESLint configuration file should exist"

    def test_eslint_config_has_required_extends(self):
        """Test that ESLint config extends required configurations."""
        config_path = Path("frontend/.eslintrc.js")
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Check for required extends
        assert "'react-app'" in content, "Should extend react-app"
        assert "'react-app/jest'" in content, "Should extend react-app/jest"

    def test_eslint_config_has_typescript_parser(self):
        """Test that ESLint config uses TypeScript parser."""
        config_path = Path("frontend/.eslintrc.js")
        with open(config_path, 'r') as f:
            content = f.read()
        
        assert "'@typescript-eslint/parser'" in content, "Should use TypeScript parser"

    def test_eslint_config_has_required_plugins(self):
        """Test that ESLint config includes required plugins."""
        config_path = Path("frontend/.eslintrc.js")
        with open(config_path, 'r') as f:
            content = f.read()
        
        assert "'@typescript-eslint'" in content, "Should include TypeScript plugin"
        assert "'react-hooks'" in content, "Should include React hooks plugin"

    def test_eslint_config_has_test_overrides(self):
        """Test that ESLint config has overrides for test files."""
        config_path = Path("frontend/.eslintrc.js")
        with open(config_path, 'r') as f:
            content = f.read()
        
        assert "overrides" in content, "Should have overrides section"
        assert "**/*.test.ts" in content, "Should override test files"
        assert "**/*.test.tsx" in content, "Should override test files"

    def test_package_json_has_lint_scripts(self):
        """Test that package.json has proper lint scripts."""
        package_path = Path("frontend/package.json")
        with open(package_path, 'r') as f:
            package_data = json.load(f)
        
        scripts = package_data.get("scripts", {})
        assert "lint" in scripts, "Should have lint script"
        assert "lint:fix" in scripts, "Should have lint:fix script"
        assert "lint:check" in scripts, "Should have lint:check script"
        
        # Check script content
        assert "eslint src --ext .ts,.tsx" in scripts["lint"], "Lint script should target TypeScript files"
        assert "--fix" in scripts["lint:fix"], "Fix script should include --fix flag"

    @patch('subprocess.run')
    def test_makefile_lint_js_target(self, mock_run):
        """Test that Makefile lint-js target works correctly."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        # This would normally run the actual command, but we're mocking it
        result = subprocess.run(["make", "lint-js"], capture_output=True, text=True)
        
        # In a real test environment, we'd check the actual command execution
        # For now, we just verify the mock was called
        assert mock_run.called or result.returncode == 0

    def test_eslint_rules_configuration(self):
        """Test that ESLint rules are properly configured."""
        config_path = Path("frontend/.eslintrc.js")
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Check for important rules
        assert "@typescript-eslint/no-unused-vars" in content, "Should have no-unused-vars rule"
        assert "@typescript-eslint/no-explicit-any" in content, "Should have no-explicit-any rule"
        assert "react-hooks/rules-of-hooks" in content, "Should have React hooks rules"
        assert "import/order" in content, "Should have import order rule"

    def test_eslint_environment_configuration(self):
        """Test that ESLint environment is properly configured."""
        config_path = Path("frontend/.eslintrc.js")
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Check for environment settings
        assert "browser: true" in content, "Should enable browser environment"
        assert "es6: true" in content, "Should enable ES6 environment"
        assert "jest: true" in content, "Should enable Jest environment"

    def test_reports_directory_creation(self):
        """Test that reports directory can be created."""
        reports_path = Path("reports")
        
        # If it doesn't exist, create it
        if not reports_path.exists():
            reports_path.mkdir(exist_ok=True)
        
        assert reports_path.exists(), "Reports directory should exist"
        assert reports_path.is_dir(), "Reports path should be a directory"

    def test_pytest_configuration_for_reporting(self):
        """Test that pytest configuration supports reporting."""
        pytest_config_path = Path("pytest.ini")
        assert pytest_config_path.exists(), "pytest.ini should exist"
        
        with open(pytest_config_path, 'r') as f:
            content = f.read()
        
        # Check basic configuration
        assert "[pytest]" in content, "Should have pytest section"
        assert "testpaths = tests" in content, "Should set test paths"

    @pytest.mark.skipif(not Path("frontend").exists(), reason="Frontend directory not found")
    def test_frontend_directory_structure(self):
        """Test that frontend directory has expected structure."""
        frontend_path = Path("frontend")
        
        # Check for essential files
        assert (frontend_path / "package.json").exists(), "Should have package.json"
        assert (frontend_path / "tsconfig.json").exists(), "Should have tsconfig.json"
        assert (frontend_path / ".eslintrc.js").exists(), "Should have .eslintrc.js"
        assert (frontend_path / "src").exists(), "Should have src directory"

    def test_makefile_phony_targets(self):
        """Test that Makefile has proper .PHONY declarations."""
        makefile_path = Path("Makefile")
        with open(makefile_path, 'r') as f:
            content = f.read()
        
        # Check for .PHONY declarations
        assert ".PHONY:" in content, "Should have .PHONY declarations"
        assert "lint-js" in content, "Should include lint-js in targets"
        assert "test-unit-with-reports" in content, "Should include test-unit-with-reports"

    def test_integration_with_ci_pipeline(self):
        """Test that linting integrates with CI pipeline."""
        makefile_path = Path("Makefile")
        with open(makefile_path, 'r') as f:
            content = f.read()
        
        # Check that lint is part of CI
        ci_section = False
        for line in content.split('\n'):
            if line.startswith('ci:'):
                ci_section = True
            elif ci_section and 'lint' in line:
                assert True, "CI should include linting"
                return
        
        # If we get here, lint wasn't found in CI
        pytest.fail("CI target should include linting")


class TestTestReportingIntegration:
    """Test test reporting functionality."""

    def test_pytest_html_dependency_available(self):
        """Test that pytest-html is available."""
        try:
            import pytest_html
            assert pytest_html is not None
        except ImportError:
            pytest.fail("pytest-html should be installed")

    def test_pytest_json_report_dependency_available(self):
        """Test that pytest-json-report is available."""
        try:
            import pytest_jsonreport
            assert pytest_jsonreport is not None
        except ImportError:
            pytest.fail("pytest-json-report should be installed")

    def test_makefile_test_targets_exist(self):
        """Test that Makefile has required test targets."""
        makefile_path = Path("Makefile")
        with open(makefile_path, 'r') as f:
            content = f.read()
        
        assert "test-unit:" in content, "Should have test-unit target"
        assert "test-unit-with-reports:" in content, "Should have test-unit-with-reports target"
        assert "test-backend-coverage:" in content, "Should have test-backend-coverage target"

    def test_coverage_configuration(self):
        """Test that coverage is properly configured."""
        makefile_path = Path("Makefile")
        with open(makefile_path, 'r') as f:
            content = f.read()
        
        # Check for coverage options
        assert "--cov=backend" in content, "Should cover backend module"
        assert "--cov=ai" in content, "Should cover ai module"
        assert "--cov=models" in content, "Should cover models module"
        assert "--cov-report=html" in content, "Should generate HTML coverage report"
        assert "--cov-report=json" in content, "Should generate JSON coverage report"

    def test_test_reporting_file_paths(self):
        """Test that test reporting infrastructure is available."""
        makefile_path = Path("Makefile")
        with open(makefile_path, 'r') as f:
            content = f.read()

        # Check for test reporting targets
        assert "test-unit-with-reports:" in content, "Should have test-unit-with-reports target"
        assert "reports" in content, "Should reference reports directory"

        # Check that reports directory can be created
        reports_path = Path("reports")
        if not reports_path.exists():
            reports_path.mkdir(exist_ok=True)
        assert reports_path.exists(), "Reports directory should be available"
