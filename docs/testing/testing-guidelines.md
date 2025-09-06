# Testing Guidelines - Steve's Mom AI Chatbot Project

## Document Information

- **Created**: 2025-09-06
- **Story**: TFA-001 - Test Frameworks Alignment Analysis
- **Purpose**: Comprehensive testing guidelines based on framework analysis and company standards
- **Compliance**: Aligned with `docs/standards/sw-testing-standard.md`
- **Last Updated**: 2025-09-06

## Overview

This document provides comprehensive testing guidelines for the Steve's Mom AI Chatbot project, ensuring alignment with company standards while addressing project-specific requirements. These guidelines are based on the TFA-001 analysis and implement the three-stage testing approach mandated by company standards.

## Testing Strategy

### Three-Stage Testing Framework

Our testing strategy follows the company-mandated three-stage approach:

1. **Unit Testing** (90% coverage requirement)
2. **Acceptance Testing** (BDD scenarios mapping to PRD)
3. **Integration Testing** (E2E automation for software-only projects)

### Framework Stack

#### Backend Testing
- **Primary Framework**: pytest (v8.3.2)
- **Coverage**: pytest-cov (v5.0.0) with 90% threshold
- **Async Support**: pytest-asyncio (v0.23.2)
- **Mocking**: pytest-mock (v3.12.0)
- **Reporting**: pytest-html (v4.1.1), pytest-json-report (v1.5.0)

#### Frontend Testing
- **Primary Framework**: Jest (via react-scripts 5.0.1)
- **Component Testing**: @testing-library/react (v14.1.2)
- **DOM Utilities**: @testing-library/jest-dom (v6.1.5)
- **User Interactions**: @testing-library/user-event (v14.5.1)

#### Acceptance Testing
- **BDD Framework**: behave (v1.2.6)
- **Feature Location**: `tests/acceptance/features/`
- **Reporting**: JSON + Executive report transformation

#### End-to-End Testing
- **Framework**: Playwright (v1.45.3)
- **Browsers**: Chromium, Firefox, WebKit
- **Test Organization**: `tests/e2e/` with specialized suites

## Test Organization

### Directory Structure
```
tests/
├── unit/                 # Backend unit tests (pytest)
│   ├── test_*.py        # Unit test files
│   └── conftest.py      # Shared fixtures
├── integration/         # Backend integration tests
├── acceptance/          # BDD acceptance tests (behave)
│   ├── features/        # Gherkin feature files
│   └── steps/           # Step definitions
├── e2e/                 # End-to-end tests (Playwright)
│   ├── core/            # Core functionality tests
│   ├── navigation/      # Navigation tests
│   └── admin/           # Admin panel tests
└── coverage/            # Coverage reports

frontend/src/
├── **/__tests__/        # Frontend component tests
└── **/*.test.tsx        # Frontend test files
```

### Naming Conventions

#### Backend Tests (Python)
- **Files**: `test_*.py` (e.g., `test_config_manager.py`)
- **Functions**: `test_should_*_when_*()` (descriptive naming)
- **Classes**: `Test*` (e.g., `TestConfigManager`)

#### Frontend Tests (TypeScript)
- **Files**: `*.test.tsx` or `*.test.ts`
- **Describe blocks**: Component or feature names
- **Test cases**: "should [expected behavior] when [condition]"

#### Acceptance Tests (Gherkin)
- **Files**: `*.feature`
- **Scenarios**: Business-focused descriptions
- **Steps**: Given/When/Then format

## Testing Standards

### Unit Testing Requirements

#### Coverage Standards
- **Minimum Coverage**: 90% statement coverage
- **Enforcement**: Automated via pytest-cov
- **Reporting**: HTML, JSON, and XML formats
- **Exclusions**: Test files, migrations, configuration

#### Test Quality Standards
- **One assertion per test** (when possible)
- **Descriptive test names** explaining behavior
- **Proper setup/teardown** using fixtures
- **Environment isolation** between tests

#### Example Unit Test
```python
def test_should_return_available_providers_when_credentials_present():
    """Test that get_available_providers returns only providers with valid credentials."""
    env = {
        "GROK_ENABLED": "true",
        "ANTHROPIC_API_KEY": "test-key",
        "LOCAL_ENABLED": "true"
    }
    with isolated_env(env):
        manager = ProviderConfigManager()
        available = manager.get_available_providers()
        
        # Should include CLAUDE (has key) and LOCAL (no key required)
        # Should exclude GROK (no key)
        assert len(available) == 2
        assert any(p.provider_type == ProviderType.CLAUDE for p in available)
        assert any(p.provider_type == ProviderType.LOCAL for p in available)
```

### Frontend Testing Requirements

#### Component Testing Standards
- **Render testing**: Verify components render without crashing
- **User interaction testing**: Test user workflows
- **State management testing**: Verify state changes
- **Accessibility testing**: Basic a11y checks

#### Example Frontend Test
```typescript
test('should display error message when API call fails', async () => {
  // Mock failed API response
  jest.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('API Error'));
  
  render(<TaskDetailPage />);
  
  // Wait for error message to appear
  const errorMessage = await screen.findByText(/failed to load task/i);
  expect(errorMessage).toBeInTheDocument();
});
```

### Acceptance Testing Requirements

#### BDD Standards
- **Feature files**: Written in business language
- **Scenario mapping**: Each scenario maps to PRD requirement
- **Step reusability**: Common steps shared across features
- **Data-driven testing**: Use scenario outlines for variations

#### Example Acceptance Test
```gherkin
Feature: AI Provider Configuration
  As a system administrator
  I want to configure AI providers
  So that the chatbot can route requests appropriately

  Scenario: Provider availability with valid credentials
    Given the GROK provider is enabled
    And a valid GROK API key is configured
    When I check available providers
    Then GROK should be listed as available
    And it should have priority 1
```

## Test Execution

### Make Targets

#### Primary Test Commands
```bash
# Run all tests
make test

# Individual test suites
make test-unit                 # Backend unit tests
make test-frontend            # Frontend Jest tests
make test-acceptance          # BDD acceptance tests
make test-e2e                # End-to-end tests

# Coverage reporting
make test-backend-coverage    # Backend with coverage
make test-frontend-coverage   # Frontend with coverage
make test-coverage           # Combined coverage

# Unified reporting
make test-unified            # All tests with unified reporting
```

#### CI/CD Integration
```bash
# Fast CI (for pull requests)
make ci-fast                 # Lint + unit tests only

# Full CI (for main branch)
make ci                      # All tests + validation
```

### Test Environment Setup

#### Backend Setup
```bash
# Install dependencies
make setup-backend setup-dev

# Environment variables
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1

# Run tests
.venv/bin/pytest tests/unit/ -v
```

#### Frontend Setup
```bash
# Install dependencies
cd frontend && npm install

# Run tests
npm test -- --watchAll=false
```

## Quality Gates

### Automated Quality Checks

#### Pre-commit Requirements
- [ ] All tests pass (unit, integration, acceptance)
- [ ] Code coverage ≥90%
- [ ] Linting passes (Python: flake8, mypy; JS: ESLint)
- [ ] No security vulnerabilities detected

#### CI/CD Pipeline Gates
- [ ] Unit test pass rate: 100%
- [ ] Coverage threshold: ≥90%
- [ ] Acceptance test pass rate: 100%
- [ ] Performance benchmarks: Within thresholds
- [ ] Security scans: No high/critical issues

### Manual Quality Checks

#### Code Review Checklist
- [ ] Tests cover edge cases and error conditions
- [ ] Test names are descriptive and clear
- [ ] No test dependencies or ordering issues
- [ ] Proper mocking and isolation
- [ ] Documentation updated for new features

## Reporting and Metrics

### Unified Test Reporting

Our unified reporting system generates two standardized reports:

#### Functionality Report (`reports/functionality-report.json`)
- Technical test results and metrics
- Coverage data across all frameworks
- Framework-specific success rates
- Compliance status with company standards

#### Executive Report (`final/executive-report.json`)
- High-level summary for stakeholders
- Overall success rates and trends
- Risk indicators and open issues
- Business impact metrics

### Key Performance Indicators

#### Quality Metrics
- **Test Pass Rate**: Target >99%
- **Coverage Percentage**: Target ≥90%
- **Defect Escape Rate**: Target <2%
- **Test Execution Time**: Target <5 minutes

#### Operational Metrics
- **Build Success Rate**: Target >95%
- **Time to Feedback**: Target <10 minutes
- **Developer Satisfaction**: Target >4.0/5.0

## Best Practices

### Test Design Principles

#### FIRST Principles
- **Fast**: Tests should run quickly
- **Independent**: Tests should not depend on each other
- **Repeatable**: Tests should produce consistent results
- **Self-Validating**: Tests should have clear pass/fail outcomes
- **Timely**: Tests should be written with or before the code

#### Test Pyramid
- **Unit Tests (70%)**: Fast, isolated, comprehensive
- **Integration Tests (20%)**: Component interactions
- **E2E Tests (10%)**: Critical user journeys

### Common Patterns

#### Test Data Management
- Use factories for test data creation
- Isolate test data between tests
- Use realistic but minimal data sets
- Avoid shared mutable state

#### Mocking Guidelines
- Mock external dependencies (APIs, databases)
- Use mocks sparingly in unit tests
- Verify mock interactions when relevant
- Prefer fakes over mocks when possible

#### Error Testing
- Test both happy path and error conditions
- Verify error messages and codes
- Test boundary conditions and edge cases
- Include security-related error scenarios

## Troubleshooting

### Common Issues

#### Test Isolation Problems
- **Symptom**: Tests pass individually but fail in suite
- **Solution**: Use proper environment isolation (see `test_config_manager.py`)
- **Prevention**: Clear environment variables between tests

#### Coverage Gaps
- **Symptom**: Coverage below 90% threshold
- **Solution**: Identify uncovered lines using HTML coverage report
- **Prevention**: Write tests alongside code development

#### Flaky Tests
- **Symptom**: Tests pass/fail inconsistently
- **Solution**: Identify timing issues, improve test isolation
- **Prevention**: Use deterministic test data and proper waits

### Debug Commands

```bash
# Run specific test with verbose output
make test-unit ARGS="-v -k test_specific_function"

# Generate coverage report
make test-backend-coverage

# Run tests with debugging
.venv/bin/pytest tests/unit/test_file.py -v -s --pdb
```

## Continuous Improvement

### Regular Reviews
- **Weekly**: Test metrics and failure analysis
- **Monthly**: Coverage trends and quality gates
- **Quarterly**: Framework updates and best practices

### Tool Updates
- Monitor framework updates and security patches
- Evaluate new testing tools and techniques
- Update guidelines based on lessons learned

### Training and Knowledge Sharing
- Regular testing workshops for team members
- Documentation of testing patterns and solutions
- Cross-team collaboration on testing strategies

---

*These guidelines are living documents that should be updated as the project evolves and new testing challenges are identified.*
