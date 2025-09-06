# Testing Guidelines

## 📋 Quick Reference

For comprehensive testing documentation, see:
- **[Testing Guidelines](../docs/testing/testing-guidelines.md)** - Complete testing standards and best practices
- **[Test Framework Inventory](../docs/testing/test-framework-inventory.md)** - Current testing tools and frameworks
- **[Gap Analysis](../docs/testing/test-framework-gap-analysis.md)** - Compliance analysis against company standards
- **[Implementation Roadmap](../docs/testing/test-framework-recommendations-roadmap.md)** - Prioritized improvement plan

## Overview

This document outlines the testing standards and patterns for the Steve's Mom AI project.

## Test Structure

```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for component interactions
├── acceptance/     # BDD acceptance tests for business requirements
└── conftest.py     # Shared pytest fixtures
```

## Test Categories

### Unit Tests
- Test individual functions, classes, and modules in isolation
- Use mocks for external dependencies
- Fast execution (< 1 second per test)
- High coverage of edge cases and error conditions

### Integration Tests
- Test component interactions and data flow
- Use real implementations but controlled environments
- Test database operations, API integrations, etc.
- Moderate execution time (< 10 seconds per test)

### Acceptance Tests
- Test complete user scenarios and business requirements
- Use BDD (Behavior-Driven Development) with Gherkin syntax
- Map directly to PRD functional requirements
- **NO MOCKS** - test real system behavior
- May have longer execution times for comprehensive scenarios

## Async Testing Patterns

### Standard Async Test Structure

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality."""
    # Arrange
    service = MyAsyncService()
    
    # Act
    result = await service.async_method()
    
    # Assert
    assert result is not None
```

### Async Fixtures

```python
@pytest.fixture
async def async_service():
    """Provide an async service instance."""
    service = MyAsyncService()
    await service.initialize()
    yield service
    await service.cleanup()
```

### Testing Async Exceptions

```python
@pytest.mark.asyncio
async def test_async_exception():
    """Test async exception handling."""
    service = MyAsyncService()
    
    with pytest.raises(ExpectedException):
        await service.failing_method()
```

## Mocking Guidelines

### Unit Tests - Use Mocks Extensively
```python
from unittest.mock import Mock, AsyncMock, patch

@patch('module.external_service')
def test_with_mock(mock_service):
    mock_service.return_value = "mocked_result"
    # Test logic here
```

### Acceptance Tests - NO MOCKS
```python
# ❌ DON'T DO THIS in acceptance tests
@patch('backend.service.ExternalAPI')
def test_user_workflow(mock_api):
    pass

# ✅ DO THIS instead
def test_user_workflow():
    # Use real implementations or test-friendly alternatives
    service = RealService()
    result = service.process_user_request()
    assert result.success
```

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_unit_functionality():
    pass

@pytest.mark.integration
def test_integration_scenario():
    pass

@pytest.mark.acceptance
def test_acceptance_criteria():
    pass

@pytest.mark.slow
def test_long_running_operation():
    pass

@pytest.mark.skip(reason="Feature not implemented")
def test_future_feature():
    pass
```

## Running Tests

### All Tests
```bash
make test
```

### Unit Tests Only
```bash
make test-unit
```

### Acceptance Tests Only
```bash
make test-acceptance
```

### Specific Test Categories
```bash
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

## Coverage Requirements

- Unit tests: Aim for 90%+ coverage
- Integration tests: Focus on critical paths
- Acceptance tests: Cover all PRD requirements

## Best Practices

1. **Test Naming**: Use descriptive names that explain the scenario
   - `test_user_login_with_valid_credentials_succeeds`
   - `test_inventory_update_with_invalid_item_raises_error`

2. **Arrange-Act-Assert**: Structure tests clearly
   ```python
   def test_example():
       # Arrange
       setup_data()
       
       # Act
       result = function_under_test()
       
       # Assert
       assert result == expected_value
   ```

3. **One Assertion Per Test**: Focus on testing one thing at a time

4. **Test Data**: Use factories or fixtures for consistent test data

5. **Error Testing**: Test both success and failure scenarios

6. **Async Patterns**: Always use `@pytest.mark.asyncio` for async tests

## Continuous Integration

Tests run automatically on:
- Pull requests
- Main branch commits
- Scheduled nightly runs

Quality gates:
- All tests must pass
- Coverage thresholds must be met
- No new linting violations

## Troubleshooting

### Common Issues

1. **Async Test Failures**: Ensure `@pytest.mark.asyncio` is used
2. **Import Errors**: Check PYTHONPATH and module structure
3. **Mock Issues**: Verify mock paths and return values
4. **Flaky Tests**: Add proper setup/teardown and avoid timing dependencies

### Getting Help

- Check test logs for detailed error messages
- Review similar working tests for patterns
- Consult team documentation and standards
