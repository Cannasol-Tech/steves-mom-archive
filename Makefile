.PHONY: help setup setup-backend setup-frontend setup-dev
.PHONY: test test-unit test-integration test-acceptance test-acceptance-pytest test-frontend test-infra test-router test-router-acceptance
.PHONY: test-coverage test-backend-coverage test-frontend-coverage test-frontend-verbose test-frontend-inband test-frontend-bail test-frontend-each
.PHONY: lint lint-py lint-js lint-md fix-lint
.PHONY: preview dev clean
.PHONY: deploy deploy-infra deploy-functions
.PHONY: ci ci-fast infra-build infra-whatif
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
	@echo "  setup-tools   - Install Azurite and Azure Functions Core Tools"
	@echo ""
	@echo "Testing:"
	@echo "  test          - Run all tests (unit + integration + acceptance)"
	@echo "  test-unit     - Run unit tests only"
	@echo "  test-integration - Run integration tests"
	@echo "  test-backend  - Run backend tests (unit + integration)"
	@echo "  test-backend-coverage - Run backend tests with coverage (backend/ ai/ models/)"
	@echo "  test-acceptance - Run acceptance tests (behave)"
	@echo "  test-acceptance-pytest - Run acceptance tests implemented with pytest"
	@echo "  test-frontend - Run frontend tests (Jest/React Testing Library)"
	@echo "  test-frontend-verbose - Run frontend tests with --verbose for detailed suite/test reporting"
	@echo "  test-frontend-inband  - Run frontend tests serially (--runInBand) and verbose to isolate failures"
	@echo "  test-frontend-bail    - Run frontend tests with --bail=1 to stop at first failure and show details"
	@echo "  test-frontend-each    - Run each frontend test file individually to isolate failing suite"
	@echo "  test-frontend-coverage - Run frontend tests with coverage"
	@echo "  test-coverage - Run backend + frontend coverage suites"
	@echo "  test-infra    - Run infrastructure tests (Bicep validation)"
	@echo "  test-router   - Run model router unit tests"
	@echo "  test-router-acceptance - Run model router acceptance tests (pytest)"
	@echo ""
	@echo "Linting & Code Quality:"
	@echo "  lint          - Run all linters (Python, JS, Markdown)"
	@echo "  lint-py       - Run Python linters (flake8, mypy)"
	@echo "  lint-js       - Run JavaScript/TypeScript linters (ESLint)"
	@echo "  lint-md       - Run markdown linting"
	@echo "  fix-lint      - Auto-fix linting issues where possible"
	@echo ""
	@echo "Development:"
	@echo "  preview       - Start local preview (installs + servers)"
	@echo "  preview-serve - Start servers only (FastAPI @9696 + Frontend @6969)"
	@echo "  preview-smoke - Smoke test: check backend (9696), frontend (6969), and proxy"
	@echo "  dev           - Start development environment with hot reload"
	@echo "  clean         - Clean build artifacts and caches"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy        - Deploy full application (infra + functions)"
	@echo "  deploy-infra  - Deploy infrastructure only (Bicep)"
	@echo "  deploy-functions - Deploy Azure Functions only"
	@echo ""
	@echo "CI Bundles:"
	@echo "  ci            - Lint + unit + integration + frontend tests (fast CI bundle)"
	@echo "  ci-fast       - Lint (py) + unit tests only (very fast)"
	@echo ""
	@echo "Infrastructure Utilities:"
	@echo "  infra-build   - Build/validate Bicep templates"
	@echo "  infra-whatif  - Run Azure what-if against current parameters"


# Setup targets
setup: setup-backend setup-frontend setup-dev setup-tools

setup-backend:
	@echo "Setting up Python backend..."
	/opt/homebrew/bin/python3.12 -m venv .venv || python3.12 -m venv .venv || python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	@if [ -f backend/requirements.txt ]; then \
		echo "Preparing backend requirements (handling torch separately for compatibility)..."; \
		TMP_REQ=$$(mktemp); \
		grep -v '^torch' backend/requirements.txt > $$TMP_REQ; \
		echo "Installing backend requirements (without torch)..."; \
		.venv/bin/pip install -r $$TMP_REQ; \
		rm -f $$TMP_REQ; \
		echo "Attempting to install a compatible torch version (CPU) as best-effort..."; \
		.venv/bin/pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.7.0" || true; \
	fi

# Minimal backend setup for local preview (installs only core deps for FastAPI app)
setup-backend-preview:
	@echo "Setting up Python backend (preview-optimized minimal deps)..."
	/opt/homebrew/bin/python3.12 -m venv .venv || python3.12 -m venv .venv || python3 -m venv .venv || true
	# Ensure python3 and python shims exist inside venv for shebang compatibility
	@if [ ! -x .venv/bin/python3 ]; then \
		PYREAL=$$(ls .venv/bin/python3* .venv/bin/python 2>/dev/null | head -n1); \
		[ -n "$$PYREAL" ] && ln -sf "$$PYREAL" .venv/bin/python3 || true; \
	fi
	@if [ ! -x .venv/bin/python ]; then \
		PYREAL=$$(ls .venv/bin/python3* .venv/bin/python 2>/dev/null | head -n1); \
		[ -n "$$PYREAL" ] && ln -sf "$$PYREAL" .venv/bin/python || true; \
	fi
	.venv/bin/pip install --upgrade pip
	@echo "Installing minimal runtime deps (FastAPI, Uvicorn, SQLAlchemy, Pydantic, Dotenv, HTTP libs)..."
	# Install with conservative pins, fallback to latest if specific versions fail
	.venv/bin/pip install "fastapi>=0.108,<0.110" || .venv/bin/pip install fastapi || true
	.venv/bin/pip install "uvicorn>=0.25,<0.29" || .venv/bin/pip install uvicorn || true
	.venv/bin/pip install "sqlalchemy>=2.0,<2.1" || .venv/bin/pip install sqlalchemy || true
	.venv/bin/pip install "pydantic>=2.8,<3" "pydantic-settings>=2.1,<3" || .venv/bin/pip install pydantic pydantic-settings || true
	.venv/bin/pip install "python-dotenv>=1.0,<2" || .venv/bin/pip install python-dotenv || true
	.venv/bin/pip install "aiohttp>=3.9,<4" "httpx>=0.26,<0.28" || true

setup-frontend:
	@echo "Setting up frontend dependencies..."
	cd frontend && npm install

setup-dev:
	@echo "Installing development dependencies..."
	.venv/bin/pip install -r requirements-dev.txt
	.venv/bin/pip install pytest-asyncio flake8 mypy black isort

# Tooling (no-op by default to avoid global installs automatically)
setup-tools:
	@echo "Skipping automatic install of Azurite and Azure Functions Core Tools."
	@echo "To install manually:"
	@echo "  npm install -g azurite"
	@echo "  brew tap azure/functions && brew install azure-functions-core-tools@4"

# Testing targets
test: setup-backend-preview setup-dev test-unit test-integration test-acceptance test-frontend

test-unit: setup-backend setup-dev
	@echo "Running unit tests..."
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -p pytest_asyncio tests/unit/ -v

test-integration: setup-backend setup-dev
	@echo "Running integration tests..."
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -p pytest_asyncio tests/integration/ -v

test-acceptance: setup-backend setup-dev
	@echo "Running acceptance tests (Behave) and generating executive report..."
	@BEHAVE_JSON=tests/acceptance/.behave-report.json; \
	mkdir -p tests/acceptance || true; \
	mkdir -p final || true; \
	EXIT_CODE=0; \
	# Run Behave with JSON output captured; preserve exit code
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/behave -f json -o $$BEHAVE_JSON tests/acceptance/features || EXIT_CODE=$$?; \
	# Transform to executive-report.json (set owner/repo; script will set releaseTag=local for non-CI runs)
	REPORT_OWNER=Cannasol-Tech REPORT_REPO=steves-mom-archive .venv/bin/python scripts/acceptance_to_executive_report.py --behave-json $$BEHAVE_JSON --out final/executive-report.json || true; \
	# Ensure artifact exists even on catastrophic failure
	[ -f final/executive-report.json ] || echo '{"version":"1.0.0","owner":"Cannasol-Tech","repo":"steves-mom-archive","releaseTag":"local","commit":"unknown","createdAt":"" ,"summary":{"total":0,"passed":0,"failed":0,"skipped":0,"durationMs":0},"scenarios":[],"requirements":[]}' > final/executive-report.json; \
	# Return original Behave exit code
	exit $$EXIT_CODE

test-acceptance-pytest: setup-backend setup-dev
	@echo "Running acceptance tests (pytest)..."
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -p pytest_asyncio tests/acceptance/*.py -v

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test -- --watchAll=false

test-frontend-verbose:
	@echo "Running frontend tests (verbose)..."
	cd frontend && npm test -- --watchAll=false --verbose

test-frontend-inband:
	@echo "Running frontend tests (in-band, verbose)..."
	cd frontend && npm test -- --watchAll=false --verbose --runInBand

test-frontend-bail:
	@echo "Running frontend tests (bail at first failure)..."
	cd frontend && npm test -- --watchAll=false --verbose --bail=1

test-frontend-each:
	@echo "Running each frontend test file individually to isolate failures..."
	@set -e; \
	FILES=$$(cd frontend && find src -type f \( -name "*.test.tsx" -o -name "*.test.ts" \) | sort); \
	for f in $$FILES; do \
	  echo "\n--- Running $$f ---"; \
	  (cd frontend && npm test -- --watchAll=false --verbose --runInBand $$f) || exit $$?; \
	done; \
	echo "All individual frontend tests passed."

# Coverage targets
test-backend-coverage: setup-backend setup-dev
	@echo "Running backend tests with coverage..."
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -p pytest_cov -p pytest_asyncio \
	  tests/unit/ tests/integration/ -v \
	  --cov=backend --cov=ai --cov=models \
	  --cov-report=term-missing \
	  --cov-report=xml:coverage-backend.xml

test-frontend-coverage:
	@echo "Running frontend tests with coverage..."
	cd frontend && npm test -- --watchAll=false --coverage

test-coverage: test-backend-coverage test-frontend-coverage
	@echo "Combined coverage complete. Backend: coverage-backend.xml, Frontend: frontend/coverage/"

test-infra: setup-dev
	@echo "Running infrastructure tests..."
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -p pytest_asyncio tests/infrastructure/ -v

# Convenience backend test bundle
test-backend: setup-backend setup-dev
	@echo "Running backend tests (unit + integration)..."
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -p pytest_asyncio tests/unit/ tests/integration/ -v

test-router: setup-backend setup-dev
	@echo "Running model router unit tests..."
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -p pytest_asyncio tests/unit/test_model_router_* -v

test-router-acceptance: setup-backend setup-dev
	@echo "Running model router acceptance tests (pytest)..."
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -p pytest_asyncio tests/acceptance/test_model_router_acceptance.py -v

# Linting targets
lint: lint-py lint-js lint-md

lint-py:
	@echo "Running Python linters..."
	.venv/bin/flake8 backend/ models/ ai/ --max-line-length=100
	.venv/bin/mypy --ignore-missing-imports

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

# -----------------------------------------------------------------------------
# All-in-one Local Preview
#
# make preview
# - Starts FastAPI backend on 127.0.0.1:9696 (also serves WebSocket at /ws)
# - Starts CRA frontend on http://localhost:6969
# - CRA proxy forwards /api/* and /ws to 127.0.0.1:9696 (see frontend/package.json)
# - Press Ctrl+C to stop both processes (trap handles cleanup)
#
# Notes:
# - The backend auto-initializes the local SQLite DB schema on startup so task
#   endpoints work out of the box (Base.metadata.create_all).
# - To enable real AI responses (instead of local placeholder), set provider keys
#   in a repo-root .env (auto-loaded by FastAPI):
#     GROK_API_KEY=...
#     OPENAI_API_KEY=...
#     ANTHROPIC_API_KEY=...
# - Requirements: Python 3.12+, Node.js 18+, run `make setup` first.
# - This target does NOT require Azurite or Azure Functions Core Tools.
# -----------------------------------------------------------------------------

# Development targets
preview: setup-backend-preview setup-frontend
	@echo "Starting local preview (FastAPI backend + Frontend)..."
	@echo "Backend (FastAPI) on http://127.0.0.1:9696 (WebSocket: /ws)"
	@echo "Frontend (CRA) on http://localhost:6969"
	@echo "Note: CRA proxies /api/* and /ws to 127.0.0.1:9696 (see frontend/package.json)"
	@echo "Press Ctrl+C to stop all"
	@trap 'kill %1 %2 2>/dev/null || true' EXIT; \
	(.venv/bin/uvicorn backend.api.app:app --host 127.0.0.1 --port 9696 --reload &) && \
	(cd frontend && BROWSER=none PORT=6969 npm start &) && \
	wait

dev: preview

# Quick smoke check for local preview stack
preview-smoke: setup-backend setup-frontend
	@bash ./scripts/preview-smoke.sh

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

# CI bundles
ci:
	@echo "Running CI bundle (lint + unit + integration + frontend)..."
	$(MAKE) lint
	$(MAKE) test-unit
	$(MAKE) test-integration
	$(MAKE) test-frontend

ci-fast:
	@echo "Running fast CI bundle (lint-py + unit)..."
	$(MAKE) lint-py
	$(MAKE) test-unit

# Infrastructure utilities
infra-build:
	@echo "Building/validating Bicep templates..."
	cd infrastructure && ./scripts/bicep-build.sh

infra-whatif:
	@echo "Running Azure what-if (non-destructive preview)..."
	cd infrastructure && ./scripts/bicep-whatif.sh

# Legacy targets (kept for compatibility)
md-fix: fix-lint
