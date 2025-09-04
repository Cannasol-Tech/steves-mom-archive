#!/bin/bash

# Clean Test Runner - Removes previous reports and runs fresh tests
# Usage: ./run-clean-tests.sh [test-pattern] [browser]
# Examples:
#   ./run-clean-tests.sh                           # Run all tests
#   ./run-clean-tests.sh user-journey              # Run user journey tests
#   ./run-clean-tests.sh user-journey firefox     # Run user journey tests on Firefox

set -e

echo "🧹 Cleaning up previous test reports..."

# Remove previous test results and reports
rm -rf test-results/
rm -rf playwright-report/

echo "✅ Previous reports cleaned"

# Determine what tests to run
TEST_PATTERN=${1:-""}
BROWSER=${2:-"chromium"}

if [ -n "$TEST_PATTERN" ]; then
    echo "🚀 Running tests matching: $TEST_PATTERN on $BROWSER"
    npx playwright test e2e/*${TEST_PATTERN}*.spec.ts --project=$BROWSER
else
    echo "🚀 Running all tests on $BROWSER"
    npx playwright test --project=$BROWSER
fi

echo ""
echo "📊 Test run complete!"
echo "📁 Fresh reports available in:"
echo "   - HTML Report: playwright-report/"
echo "   - Test Results: test-results/"
echo ""
echo "🌐 To view the HTML report, run:"
echo "   npx playwright show-report"
