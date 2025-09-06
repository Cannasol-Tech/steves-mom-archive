# Test Framework Inventory - Steve's Mom AI Chatbot Project

## Document Information

- **Created**: 2025-09-06
- **Story**: TFA-001 - Test Frameworks Alignment Analysis
- **Purpose**: Complete inventory of all testing frameworks and tools in use
- **Last Updated**: 2025-09-06

## Executive Summary

This document provides a comprehensive inventory of all testing frameworks, tools, and configurations currently deployed in the Steve's Mom AI Chatbot project. The analysis covers backend Python testing, frontend JavaScript/TypeScript testing, end-to-end testing, code quality tools, and CI/CD integration.

## Backend Testing Framework Stack

### Core Testing Framework
- **pytest (v8.3.2)** - Primary Python testing framework
  - Configuration: `pytest.ini` in project root
  - Plugin management: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` for controlled loading
  - Test discovery: `tests/unit/` directory structure

### BDD/Acceptance Testing
- **behave (v1.2.6)** - Behavior-Driven Development framework
  - Features location: `tests/acceptance/features/`
  - JSON reporting: `.behave-report.json`
  - Executive report generation: `scripts/acceptance_to_executive_report.py`

### Testing Extensions & Plugins
- **pytest-asyncio (v0.23.2)** - Async testing support
- **pytest-cov (v5.0.0)** - Code coverage measurement
- **pytest-mock (v3.12.0)** - Mocking capabilities
- **pytest-html (v4.1.1)** - HTML test reporting
- **pytest-json-report (v1.5.0)** - JSON test reporting (✅ Already installed)

### Additional Testing Dependencies
- **alembic (v1.13.1)** - Database migration testing
- **httpx (v0.27.0)** - HTTP client testing

## Frontend Testing Framework Stack

### Core Testing Framework
- **Jest** - JavaScript testing framework (via react-scripts 5.0.1)
  - Configuration: Embedded in react-scripts
  - Test runner: `npm test` command
  - Watch mode: Disabled in CI (`--watchAll=false`)

### React Testing Libraries
- **@testing-library/react (v14.1.2)** - React component testing
- **@testing-library/jest-dom (v6.1.5)** - DOM testing utilities
- **@testing-library/user-event (v14.5.1)** - User interaction simulation
- **@types/jest (v30.0.0)** - TypeScript definitions for Jest

### End-to-End Testing
- **@playwright/test (v1.45.3)** - Browser automation testing
  - Configuration: `tests/playwright.config.ts`
  - Multi-browser support: Chromium, Firefox, WebKit
  - Test organization: `tests/e2e/` directory
  - Specialized test suites: core, navigation, admin, ui, interactive, accessibility, errors, smoke

## Code Quality & Linting Tools

### Python Code Quality
- **flake8 (v7.0.0)** - Python linting
  - Configuration: `--max-line-length=100`
  - Target directories: `backend/`, `models/`, `ai/`
- **mypy (v1.8.0)** - Python type checking
  - Configuration: `mypy.ini`
  - Flag: `--ignore-missing-imports`
- **black (v23.12.1)** - Python code formatting
- **isort** - Python import sorting

### JavaScript/TypeScript Code Quality
- **ESLint** - JavaScript/TypeScript linting
  - Configuration: Extends `react-app` and `react-app/jest`
  - Scripts: `lint`, `lint:fix`, `lint:check`
  - Current status: ⚠️ 35 warnings (0 errors)

### Documentation Linting
- **markdownlint** - Markdown documentation linting
  - Configuration: `.markdownlint.yaml`
  - Target: Documentation files across the project

## Test Execution & Make Targets

### Comprehensive Test Targets
```makefile
# Primary test execution
test                    # Run all tests (unit + integration + acceptance + frontend)
test-unit              # Backend unit tests only
test-integration       # Backend integration tests
test-acceptance        # BDD acceptance tests (behave)
test-frontend          # Frontend Jest tests

# Coverage reporting
test-backend-coverage  # Backend tests with coverage
test-frontend-coverage # Frontend tests with coverage
test-coverage         # Combined coverage reporting

# Specialized testing
test-infra            # Infrastructure/Bicep validation
test-router           # Model router specific tests
test-acceptance-pytest # Pytest-based acceptance tests
```

### CI/CD Integration Targets
```makefile
ci                    # Full CI bundle (lint + all tests)
ci-fast              # Fast CI (lint-py + unit only)
```

## Current Test Execution Status

### Backend Unit Tests (Latest Run)
- **Total Tests**: 423 collected
- **Results**: 218 passed, 202 skipped, 3 failed
- **Execution Time**: 1.34 seconds
- **Failed Tests**: 3 failures in `test_config_manager.py`
- **Warnings**: 222 warnings (primarily deprecation warnings)

### Frontend Tests (Latest Run)
- **Test Suites**: 19 passed, 19 total
- **Tests**: 77 passed, 77 total
- **Execution Time**: 2.507 seconds
- **Status**: ✅ All tests passing

### Code Quality Status
- **Python Linting**: ❌ 1 mypy error in `backend/features/feature_registry.py`
- **Frontend Linting**: ⚠️ 35 ESLint warnings (0 errors)
- **Markdown Linting**: Not executed in current analysis

## Test Reporting & Metrics

### Current Reporting Capabilities
- **Backend**: JSON and HTML reporting via pytest plugins
- **Frontend**: Jest built-in reporting
- **E2E**: Playwright HTML reports
- **Acceptance**: Behave JSON + Executive report transformation
- **Coverage**: XML, JSON, and HTML formats

### Executive Reporting
- **Location**: `final/executive-report.json`
- **Generator**: `scripts/acceptance_to_executive_report.py`
- **Validation**: `scripts/validate_executive_report.py`
- **Display**: `scripts/display_executive_summary.py`

## Infrastructure & Configuration Files

### Key Configuration Files
- `pytest.ini` - Pytest configuration
- `mypy.ini` - MyPy type checking configuration
- `frontend/package.json` - Frontend dependencies and scripts
- `tests/package.json` - E2E testing dependencies
- `tests/playwright.config.ts` - Playwright configuration
- `requirements-dev.txt` - Python development dependencies
- `.markdownlint.yaml` - Markdown linting rules

### Directory Structure
```
tests/
├── unit/           # Backend unit tests (423 tests)
├── integration/    # Backend integration tests
├── acceptance/     # BDD acceptance tests
├── e2e/           # End-to-end Playwright tests
├── infrastructure/ # Infrastructure validation tests
└── coverage/      # Coverage reports

frontend/src/
├── **/__tests__/  # Frontend component tests
└── **/*.test.tsx  # Frontend test files
```

## Dependencies & Package Management

### Python Dependencies (requirements-dev.txt)
All testing dependencies are properly managed through pip and virtual environment:
- Core testing: pytest, behave
- Extensions: pytest-asyncio, pytest-cov, pytest-mock, pytest-html, pytest-json-report
- Database: alembic
- HTTP testing: httpx

### Frontend Dependencies (package.json)
Testing dependencies managed through npm:
- React testing: @testing-library suite
- E2E testing: @playwright/test
- Type definitions: @types/jest, @types/node

## Integration Points

### CI/CD Pipeline Integration
- Make targets provide standardized test execution
- Executive reporting for stakeholder visibility
- Coverage thresholds enforced
- Multi-layer testing strategy (unit → integration → acceptance → e2e)

### Development Workflow Integration
- Pre-commit hooks capability (configured but not detailed in current analysis)
- Local development testing via `make preview` and test targets
- Hot reload support for development environment

## Identified Gaps & Issues

### High Priority Issues
1. **3 failing unit tests** in `test_config_manager.py`
2. **1 mypy error** in `backend/features/feature_registry.py`
3. **35 ESLint warnings** in frontend code

### Medium Priority Improvements
1. **Deprecation warnings** (222 warnings in backend tests)
2. **Console statements** in frontend code (ESLint warnings)
3. **TypeScript any types** usage (ESLint warnings)

### Framework Alignment Opportunities
1. **Unified reporting** across all test frameworks
2. **Performance testing** framework establishment
3. **Security testing** automation integration

## Compliance Assessment

### Company Standards Alignment
- ✅ **Multi-layer testing**: Unit, integration, acceptance, e2e
- ✅ **Coverage reporting**: Multiple formats available
- ✅ **Make targets**: Standardized execution commands
- ✅ **CI/CD integration**: Comprehensive test bundles
- ⚠️ **Code quality**: Some linting violations present
- ⚠️ **Test reliability**: 3 failing unit tests need resolution

### Testing Framework Maturity
- **Backend**: Mature, comprehensive setup with minor issues
- **Frontend**: Solid foundation with linting improvements needed
- **E2E**: Well-structured Playwright implementation
- **Reporting**: Good foundation, unified reporting opportunity identified

---

*This inventory serves as the foundation for the TFA-001 gap analysis and improvement roadmap.*
