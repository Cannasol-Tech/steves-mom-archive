.PHONY: help md-lint md-fix preview setup-backend setup-frontend

# Markdownlint targets using markdownlint-cli2 and markdownlint-cli (for --fix)
# Leverages repository configs:
# - .markdownlint.yaml (rules)
# - .markdownlint-cli2.jsonc (globs/ignores)

help:
	@echo "Available targets:"
	@echo "  preview      - Start both frontend and backend servers with all dependencies"
	@echo "  setup-backend - Setup Python venv and install backend dependencies"
	@echo "  setup-frontend - Install frontend npm dependencies"
	@echo "  md-lint      - Run markdownlint on first-party docs using repo config"
	@echo "  md-fix       - Auto-fix markdown issues where possible"

md-lint:
	npx -y markdownlint-cli2 --config .markdownlint.yaml

setup-backend:
	@echo "Setting up Python backend..."
	/opt/homebrew/bin/python3.12 -m venv .venv || python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install fastapi uvicorn[standard] python-dotenv pydantic xai-sdk

setup-frontend:
	@echo "Setting up frontend dependencies..."
	cd frontend && npm install

preview: setup-backend setup-frontend
	@echo "Starting preview servers..."
	@echo "Backend will run on http://127.0.0.1:8000"
	@echo "Frontend will run on http://localhost:3000"
	@echo "Press Ctrl+C to stop both servers"
	@trap 'kill %1 %2 2>/dev/null || true' EXIT; \
	(.venv/bin/uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --reload &) && \
	(cd frontend && npm start &) && \
	wait

md-fix:
	npx -y markdownlint-cli --config .markdownlint.yaml --fix \
		"README.md" "docs/**/*.md" "infrastructure/**/*.md" "frontend/README.md" \
		--ignore "node_modules/**" --ignore ".venv/**" --ignore "venv/**" \
		--ignore "env/**" --ignore "venv312/**"
