---
description: Repository structure, branching strategy, PR/CI policy, and protections
---

# Repository Structure and Collaboration Policy

## Top-level Structure

- frontend/
- backend/
- infrastructure/
- tests/
- docs/
- scripts/
- alembic/

## Branching Strategy

- Work branch: agent-dev
- Feature branches: feature/<scope>
- Fix branches: fix/<scope>
- Chore/Docs: chore/<scope>, docs/<scope>
- Releases: release/x.y.z
- Hotfixes: hotfix/<scope>

Commit format: `[Agent-ID] type(scope): description`

## Pull Request Policy

- Target branch: agent-dev
- Include: summary, scope, test results, coverage, affected files, links to tasks in `docs/planning/implementation-plan.md`
- Require: green CI, reviewer approval per repo settings

## CI/CD Gates (Makefile)

- Lint: `make lint` (python, js/ts, markdown); autofix via `make fix`
- Tests: `make test` (unit + integration + frontend)
- Infra validation: `make whatif` when infra files change
- Acceptance/E2E (optional): `make acceptance`
- Deploy: `make deploy-infra`, `make deploy-functions`, `make deploy`

## Naming Conventions

- Frontend paths/files: kebab-case
- Python: snake_case
- Bicep modules: `infrastructure/modules/<service>.bicep`
- Tests:
  - Backend unit: `tests/unit/test_*.py`
  - Backend integration: `tests/integration/test_*.py`
  - Infra: `tests/infrastructure/test_*.py`
  - Frontend RTL: `frontend/src/**/__tests__/*.test.tsx`

## Protections and Policies

- Protect `agent-dev`: PR required + passing checks
- Enforce conventional commit + agent ID prefix in review
- Optional: code owners for critical paths (infra, backend/api, frontend/src/services)

## References

- Implementation plan: `docs/planning/implementation-plan.md` (section 1.4.1)
- Multi-agent coordination: `docs/planning/multi-agent-sync.md`
