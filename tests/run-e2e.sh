#!/bin/bash

# End-to-End Test Runner for Steve's Mom AI
# Usage: ./run-e2e.sh [category] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
CATEGORY=""
BROWSER="chromium"
HEADED=false
DEBUG=false
REPORT=false

# Function to display usage
usage() {
    echo -e "${BLUE}End-to-End Test Runner${NC}"
    echo ""
    echo "Usage: $0 [category] [options]"
    echo ""
    echo "Categories:"
    echo "  all           - Run all tests (default)"
    echo "  core          - Core functionality (chat, streaming, preview)"
    echo "  navigation    - Navigation and routing tests"
    echo "  admin         - Admin panel functionality"
    echo "  ui            - UI/UX features (theme, responsive)"
    echo "  interactive   - Interactive features (model selection, tasks)"
    echo "  accessibility - Accessibility compliance tests"
    echo "  errors        - Error handling scenarios"
    echo "  smoke         - Quick smoke tests"
    echo ""
    echo "Options:"
    echo "  --browser=BROWSER    Browser to use (chromium, firefox, webkit, mobile-chrome, mobile-safari)"
    echo "  --headed             Run in headed mode (visible browser)"
    echo "  --debug              Run in debug mode"
    echo "  --report             Generate and show HTML report"
    echo "  --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 core                           # Run core functionality tests"
    echo "  $0 all --browser=firefox          # Run all tests in Firefox"
    echo "  $0 accessibility --headed         # Run accessibility tests with visible browser"
    echo "  $0 smoke --report                 # Run smoke tests and show report"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        all|core|navigation|admin|ui|interactive|accessibility|errors|smoke)
            CATEGORY="$1"
            shift
            ;;
        --browser=*)
            BROWSER="${1#*=}"
            shift
            ;;
        --headed)
            HEADED=true
            shift
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        --report)
            REPORT=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# Set default category if none provided
if [[ -z "$CATEGORY" ]]; then
    CATEGORY="all"
fi

# Build Playwright command
PLAYWRIGHT_CMD="npx playwright test"

# Add browser project
PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --project=$BROWSER"

# Add headed mode if requested
if [[ "$HEADED" == true ]]; then
    PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --headed"
fi

# Add debug mode if requested
if [[ "$DEBUG" == true ]]; then
    PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --debug"
fi

# Define test files for each category
get_test_files() {
    case "$1" in
        "all")
            echo "*.spec.ts"
            ;;
        "core")
            echo "chat.spec.ts preview.spec.ts streaming.spec.ts"
            ;;
        "navigation")
            echo "navigation.spec.ts"
            ;;
        "admin")
            echo "admin.spec.ts"
            ;;
        "ui")
            echo "theme.spec.ts navigation.spec.ts"
            ;;
        "interactive")
            echo "model-selection.spec.ts task-approval.spec.ts"
            ;;
        "accessibility")
            echo "accessibility.spec.ts"
            ;;
        "errors")
            echo "error-handling.spec.ts"
            ;;
        "smoke")
            echo "preview.spec.ts navigation.spec.ts"
            ;;
        *)
            echo ""
            ;;
    esac
}

# Get test files for the selected category
TEST_FILES=$(get_test_files "$CATEGORY")

if [[ -z "$TEST_FILES" ]]; then
    echo -e "${RED}Unknown category: $CATEGORY${NC}"
    usage
    exit 1
fi

# Display test run information
echo -e "${BLUE}🚀 Running E2E Tests${NC}"
echo -e "${YELLOW}Category:${NC} $CATEGORY"
echo -e "${YELLOW}Browser:${NC} $BROWSER"
echo -e "${YELLOW}Test Files:${NC} $TEST_FILES"
echo ""

# Check if we're in the tests directory
if [[ ! -f "playwright.config.ts" ]]; then
    echo -e "${RED}Error: Must be run from the tests directory${NC}"
    echo "Current directory: $(pwd)"
    echo "Expected: .../tests"
    exit 1
fi

# Run the tests
echo -e "${GREEN}Starting test execution...${NC}"
echo ""

# Execute the command
if [[ "$TEST_FILES" == "*.spec.ts" ]]; then
    # Run all tests
    eval "$PLAYWRIGHT_CMD"
else
    # Run specific test files
    eval "$PLAYWRIGHT_CMD $TEST_FILES"
fi

TEST_EXIT_CODE=$?

# Generate and show report if requested
if [[ "$REPORT" == true && $TEST_EXIT_CODE -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}Generating test report...${NC}"
    npx playwright show-report
fi

# Display results
echo ""
if [[ $TEST_EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed (exit code: $TEST_EXIT_CODE)${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting tips:${NC}"
    echo "1. Check if backend is running on port 9696"
    echo "2. Check if frontend is running on port 6969"
    echo "3. Verify /api/health endpoint is accessible"
    echo "4. Run with --debug flag for detailed debugging"
    echo "5. Check test logs for specific error messages"
fi

exit $TEST_EXIT_CODE
