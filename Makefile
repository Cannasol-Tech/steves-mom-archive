.PHONY: help md-lint md-fix

# Markdownlint targets using markdownlint-cli2 and markdownlint-cli (for --fix)
# Leverages repository configs:
# - .markdownlint.yaml (rules)
# - .markdownlint-cli2.jsonc (globs/ignores)

help:
	@echo "Available targets:"
	@echo "  md-lint  - Run markdownlint on first-party docs using repo config"
	@echo "  md-fix   - Auto-fix markdown issues where possible"

md-lint:
	npx -y markdownlint-cli2 --config .markdownlint.yaml

md-fix:
	npx -y markdownlint-cli --config .markdownlint.yaml --fix \
		"README.md" "docs/**/*.md" "infrastructure/**/*.md" "frontend/README.md" \
		--ignore "node_modules/**" --ignore ".venv/**" --ignore "venv/**" \
		--ignore "env/**" --ignore "venv312/**"
