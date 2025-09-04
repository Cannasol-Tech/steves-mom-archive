# End-to-End Test Suite

This directory contains comprehensive end-to-end tests for Steve's Mom AI application using Playwright.

## Test Files Overview

### Core Functionality Tests

- **`chat.spec.ts`** - Core chat functionality with streaming responses
- **`preview.spec.ts`** - Basic preview stack functionality and health checks
- **`streaming.spec.ts`** - Advanced streaming functionality, cancellation, and retry

### Navigation and UI Tests

- **`navigation.spec.ts`** - Page navigation, routing, and mobile menu
- **`admin.spec.ts`** - Admin panel functionality and feature toggles
- **`tasks.spec.ts`** - Task analytics page and data loading
- **`theme.spec.ts`** - Theme switching and persistence

### Interactive Features

- **`model-selection.spec.ts`** - AI model selection and configuration
- **`task-approval.spec.ts`** - Task approval workflow and WebSocket updates
- **`error-handling.spec.ts`** - Error scenarios and graceful degradation

### Quality Assurance

- **`accessibility.spec.ts`** - Accessibility compliance and keyboard navigation

## Test Categories

### 🚀 Core Features
- Chat interface and messaging
- Streaming AI responses
- Model selection and configuration
- Real-time updates via WebSocket

### 🧭 Navigation & Routing
- Page navigation between Chat, Admin, and Tasks
- Mobile responsive navigation
- 404 error handling
- Browser back/forward navigation

### ⚙️ Admin Features
- Feature toggle controls
- System status monitoring
- Performance metrics display
- Quick action buttons

### 📊 Analytics & Tasks
- Task analytics data loading
- Task approval/rejection workflow
- Real-time task status updates
- Error handling for API failures

### 🎨 UI/UX Features
- Light/dark theme switching
- Theme persistence across sessions
- Responsive design across devices
- Loading states and indicators

### ♿ Accessibility
- Keyboard navigation
- Screen reader compatibility
- ARIA attributes and labels
- Focus management
- Color contrast compliance

### 🛡️ Error Handling
- API error responses
- Network failures
- Malformed data handling
- Timeout scenarios
- WebSocket connection errors

## Running Tests

### Run All Tests
```bash
cd tests
npx playwright test
```

### Run Specific Test File
```bash
npx playwright test chat.spec.ts
npx playwright test admin.spec.ts
```

### Run Tests by Category
```bash
# Core functionality
npx playwright test chat.spec.ts preview.spec.ts streaming.spec.ts

# Navigation and UI
npx playwright test navigation.spec.ts admin.spec.ts tasks.spec.ts theme.spec.ts

# Interactive features
npx playwright test model-selection.spec.ts task-approval.spec.ts

# Quality assurance
npx playwright test accessibility.spec.ts error-handling.spec.ts
```

### Run Tests in Different Browsers
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
npx playwright test --project=mobile-chrome
npx playwright test --project=mobile-safari
```

### Debug Mode
```bash
npx playwright test --debug
npx playwright test --headed
```

### Generate Test Report
```bash
npx playwright test --reporter=html
npx playwright show-report
```

## Test Configuration

The tests are configured in `playwright.config.ts` with:

- **Timeout**: 120 seconds per test
- **Retries**: 2 in CI, 1 locally
- **Browsers**: Chrome, Firefox, Safari, Mobile Chrome, Mobile Safari
- **Base URL**: http://localhost:6969
- **Screenshots**: On failure only
- **Video**: On failure only
- **Trace**: On failure only

## Prerequisites

Before running tests, ensure:

1. **Backend is running** on port 9696
2. **Frontend is running** on port 6969
3. **Health endpoint** `/api/health` is accessible
4. **Environment variables** are properly configured

The test suite automatically starts the preview stack using `../scripts/preview-serve.sh`.

## Test Data and Mocking

Tests use mocked API responses for:
- Chat API responses
- Task analytics data
- Task approval/rejection
- WebSocket connections
- Error scenarios

This ensures tests are:
- **Fast** - No real API calls
- **Reliable** - Predictable responses
- **Isolated** - No external dependencies

## Best Practices

### Writing New Tests

1. **Use descriptive test names** that explain what is being tested
2. **Group related tests** in `test.describe()` blocks
3. **Use proper selectors** - prefer role-based selectors over CSS
4. **Mock external dependencies** for reliability
5. **Test both happy path and error scenarios**
6. **Include accessibility checks** where relevant

### Test Structure

```typescript
test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup common to all tests
    await page.goto('/');
  });

  test('should do something specific', async ({ page }) => {
    // Arrange
    // Act
    // Assert
  });
});
```

### Selectors Priority

1. **Role-based**: `page.getByRole('button', { name: 'Submit' })`
2. **Label-based**: `page.getByLabelText('Email address')`
3. **Text-based**: `page.getByText('Welcome')`
4. **Test ID**: `page.getByTestId('submit-button')`
5. **CSS selectors**: Only as last resort

## Continuous Integration

Tests run automatically on:
- Pull requests
- Main branch commits
- Scheduled nightly runs

CI configuration includes:
- Multiple browser testing
- Parallel execution
- Artifact collection (screenshots, videos, traces)
- Test result reporting

## Troubleshooting

### Common Issues

1. **Tests timing out**: Increase timeout or check if services are running
2. **Flaky tests**: Add proper waits and use `expect.poll()` for dynamic content
3. **Selector not found**: Use Playwright inspector to debug selectors
4. **WebSocket errors**: Check if backend WebSocket endpoint is available

### Debug Commands

```bash
# Run with debug mode
npx playwright test --debug

# Generate trace
npx playwright test --trace=on

# Show test report
npx playwright show-report

# Record new test
npx playwright codegen localhost:6969
```

## Coverage

The test suite covers:
- ✅ All major user journeys
- ✅ Error scenarios and edge cases
- ✅ Accessibility requirements
- ✅ Cross-browser compatibility
- ✅ Mobile responsiveness
- ✅ Real-time features
- ✅ API integration points

This comprehensive test suite ensures the application works reliably across all supported browsers and devices while maintaining high quality and accessibility standards.
