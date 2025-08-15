.PHONY: help setup setup-backend setup-frontend setup-dev
.PHONY: test test-unit test-integration test-acceptance test-frontend test-infra
.PHONY: lint lint-py lint-js lint-md fix-lint
.PHONY: preview dev clean
.PHONY: deploy deploy-infra deploy-functions
.PHONY: md-lint md-fix

# Main help target
help:
	@echo "Steve's Mom AI - Available Make Targets:"
	@echo ""
	@echo "Setup & Environment:"
	@echo "  setup         - Complete project setup (backend + frontend + dev deps)"
	@echo "  setup-backend - Setup Python venv and install backend dependencies"
	@echo "  setup-frontend- Install frontend npm dependencies"
	@echo "  setup-dev     - Install development dependencies (pytest, linting, etc.)"
	@echo ""
	@echo "Testing:"
	@echo "  test          - Run all tests (unit + integration + acceptance)"
	@echo "  test-unit     - Run unit tests only"
	@echo "  test-integration - Run integration tests"
	@echo "  test-acceptance - Run acceptance tests (behave)"
	@echo "  test-frontend - Run frontend tests (Jest/React Testing Library)"
	@echo "  test-infra    - Run infrastructure tests (Bicep validation)"
	@echo ""
	@echo "Linting & Code Quality:"
	@echo "  lint          - Run all linters (Python, JS, Markdown)"
	@echo "  lint-py       - Run Python linters (flake8, mypy)"
	@echo "  lint-js       - Run JavaScript/TypeScript linters (ESLint)"
	@echo "  lint-md       - Run markdown linting"
	@echo "  fix-lint      - Auto-fix linting issues where possible"
	@echo ""
	@echo "Development:"
	@echo "  preview       - Start dev servers (backend + frontend)"
	@echo "  dev           - Start development environment with hot reload"
	@echo "  clean         - Clean build artifacts and caches"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy        - Deploy full application (infra + functions)"
	@echo "  deploy-infra  - Deploy infrastructure only (Bicep)"
	@echo "  deploy-functions - Deploy Azure Functions only"


# Setup targets
setup: setup-backend setup-frontend setup-dev

setup-backend:
	@echo "Setting up Python backend..."
	python3 -m venv .venv || /opt/homebrew/bin/python3.12 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install fastapi uvicorn[standard] python-dotenv pydantic xai-sdk

setup-frontend:
	@echo "Setting up frontend dependencies..."
	cd frontend && npm install

setup-dev:
	@echo "Installing development dependencies..."
	.venv/bin/pip install -r requirements-dev.txt
	.venv/bin/pip install pytest-asyncio flake8 mypy black isort

# Testing targets
test: test-unit test-integration test-acceptance

test-unit:
	@echo "Running unit tests..."
	.venv/bin/pytest tests/unit/ -v

test-integration:
	@echo "Running integration tests..."
	.venv/bin/pytest tests/integration/ -v

test-acceptance:
	@echo "Running acceptance tests..."
	.venv/bin/behave tests/acceptance/

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test -- --watchAll=false

test-infra:
	@echo "Running infrastructure tests..."
	.venv/bin/pytest tests/infrastructure/ -v

# Linting targets
lint: lint-py lint-js lint-md

lint-py:
	@echo "Running Python linters..."
	.venv/bin/flake8 backend/ models/ ai/ --max-line-length=100
	.venv/bin/mypy backend/ models/ ai/ --ignore-missing-imports

lint-js:
	@echo "Running JavaScript/TypeScript linters..."
	cd frontend && npm run lint

lint-md:
	@echo "Running markdown linting..."
	npx -y markdownlint-cli2 --config .markdownlint.yaml

fix-lint:
	@echo "Auto-fixing linting issues..."
	.venv/bin/black backend/ models/ ai/
	.venv/bin/isort backend/ models/ ai/
	cd frontend && npm run lint:fix
	npx -y markdownlint-cli --config .markdownlint.yaml --fix \
		"README.md" "docs/**/*.md" "infrastructure/**/*.md" "frontend/README.md" \
		--ignore "node_modules/**" --ignore ".venv/**" --ignore "venv/**" \
		--ignore "env/**" --ignore "venv312/**"

# Development targets
preview: setup-backend setup-frontend
	@echo "Starting preview servers..."
	@echo "Backend will run on http://127.0.0.1:8000"
	@echo "Frontend will run on http://localhost:3000"
	@echo "Press Ctrl+C to stop both servers"
	@trap 'kill %1 %2 2>/dev/null || true' EXIT; \
	(.venv/bin/uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --reload &) && \
	(cd frontend && npm start &) && \
	wait

dev: preview

clean:
	@echo "Cleaning build artifacts and caches..."
	rm -rf .venv/
	rm -rf frontend/node_modules/
	rm -rf frontend/build/
	rm -rf backend/__pycache__/
	rm -rf models/__pycache__/
	rm -rf ai/__pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Deployment targets
deploy: deploy-infra deploy-functions

deploy-infra:
	@echo "Deploying infrastructure..."
	cd infrastructure && ./scripts/bicep-deploy.sh

deploy-functions:
	@echo "Deploying Azure Functions..."
	cd scripts && ./deploy-azure-resources.sh

# Legacy targets (kept for compatibility)
md-fix: fix-lint
