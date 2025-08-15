# Implementation Plan: Steve's Mom AI Chatbot (MVP)

This plan follows the 2-week MVP timeline from PRD section 18.1 and your DoD: each section must conclude with 100% passing unit, integration, and acceptance tests (pytest/behave) mapped to PRD requirements in `docs/prd-v1.0.0`.

Current constraints/choices:

- Azure Functions on Consumption (or Flex Consumption On‑Demand with 0 Always Ready) for lowest cost; avoid Premium for MVP.
- NL→SQL limited to Inventory only using whitelisted query templates and guardrails.
- Privacy‑safe telemetry by default (no raw content retained; sampling disabled by default).
- Publish a release‑pack consumable by `functionality-reports` (spec TBD; placeholder implemented in MVP).
- **REQUIRED**: Cannasol logo (`/Users/Stephen/Documents/GitHub/steves-mom-archive/cannasol-logo.png`) must be integrated throughout the interface for corporate branding.

## Current Task Tagging

Current Task Tagging: Tag the task/subtask you are actively working on with [CURRENT-TASK]. Always move this tag to the next active item once the current one is complete.

## Task Tagging

Task Tagging: Tag each task/subtask with the agent ID and timestamp when it is checked out. For example, `- [ ] Task description **[CHECKED OUT: Agent-ID @timestamp]**`.

## Task Completion Tagging

Task Completion Tagging: Tag each task/subtask with the agent ID and timestamp when it is completed. For example, `- [x] Task description ✅ **[COMPLETED: Agent-ID @timestamp]**`.

## Branch Tagging

Branch Tagging: Tag each branch with the agent ID and timestamp when it is checked out. For example, `feature/descriptive-feature-name **[CHECKED OUT: Agent-ID @timestamp]**`.

## Branch Completion Tagging

Branch Completion Tagging: Tag each branch with the agent ID and timestamp when it is completed. For example, `feature/descriptive-feature-name **[COMPLETED: Agent-ID @timestamp]**`.  

## Task Dependencies

Task Dependencies: Tag each task/subtask with the agent ID and timestamp when it is checked out. For example, `- [ ] Task description **[DEPENDING ON: Agent-ID @timestamp]**`.

## Multi-Agent Coordination (from `.github/multi-agent-collaboration.prompt.md`)

- **Active Agent:** cascade-01 (registered 2025-08-13T16:55:16-04:00)

- **Checkout format:**

```markdown
- [ ] Task description **[CHECKED OUT: cascade-01 @YYYY-MM-DDThh:mm:ss-04:00] [feature/descriptive-branch]**
```

### Test Results (append entries as tasks complete)

| Task ID | Agent | Unit Tests | Integration Tests | Acceptance Tests | Coverage |
|---------|-------|------------|-------------------|------------------|----------|
| 3.T | cascade-01 | 12/12 ✅ | N/A | N/A | N/A |
| 3.4 | cascade-02 | ✅ (unit only) | N/A | N/A | N/A |
| 3.5 | cascade-02 | 1/1 ✅ | 1/1 ✅ | N/A | N/A |
| 3.6 | cascade-02 | 5/5 ✅ | N/A | N/A | N/A |
| 3.7.T | cascade-02 | 6/6 ✅ | N/A | N/A | N/A |
| 5.4.T | cascade-01 | N/A | ✅ (frontend RTL integration) | N/A | N/A |

### Completed Tasks

| Task ID | Agent | Branch | Duration | Files Modified | Merged |
|---------|-------|--------|----------|----------------|--------|
| 4.1 | augment-01 | feature/ai-provider-clients | 45min | 7 files | ✅ |

### Communication Log

| Timestamp | From | To | Message | Action Required |
|-----------|------|----|---------|-----------------|
| 2025-08-13T19:45:00-04:00 | augment-01 | ALL | Task 4.1 complete: Built comprehensive AI provider abstraction layer with GROK provider and placeholders for OpenAI, Claude, and Local models. Includes configuration management, credential handling, and provider fallback system. All tests passing. | Ready for integration with existing AI agent |
| 2025-08-15T17:25:00-04:00 | cascade-01 | ALL | Lint suite green (Python flake8+mypy scoped to backend/, JS, Markdown). Backend tests: 92 passing; Frontend tests: 46 passing. Static Web App configuration finalized; docs updated. | None |

### Implementation Plan

## 1: Infrastructure setup (Consumption plan) [ ] (est: 2 days)

### Definition of Done — Section 1 (Infrastructure)

- All IaC changes pass unit/integration tests in `tests/infrastructure/` and what-if checks are clean.
- Acceptance tests written using behave framework with Gherkin syntax for business-readable scenarios.
- Lint/format checks pass (Bicep build, scripts shellcheck as applicable).
- Azure resources provision successfully in dev; parameters documented in `infrastructure/parameters/*.json`.
- Security/Naming: follows `docs/architecture/naming.md`; soft-delete/retention settings verified.
- Docs updated: `docs/architecture/*` and `docs/deployment/azure-deployment-guide.md`.
- Planning updated: `docs/planning/implementation-plan.md` and `docs/planning/multi-agent-sync.md`.

> Hosting note: Using Azure Functions Consumption (or Flex On‑Demand) for MVP to minimize cost. PRD Appendix mentions Functions Premium; evaluate upgrade after MVP acceptance.

#### 1.1: Azure resources IaC draft (naming, SKUs) [x] (est: 0.5d) ✅ **[COMPLETED: cascade-01 @2025-08-13T17:45:00-04:00] [feature/infrastructure-iac-draft]**

- **1.1.1** [x] Define TDD scope for IaC: write test plan for naming rules and SKU validation (unit/integration)
- **1.1.2** [x] Establish naming conventions (resource group, functions, storage, sql, redis, kv) with examples and doc in `docs/architecture/naming.md`
- **1.1.3** [x] Select SKUs for each service (Functions Consumption/Flex, SQL tier, Redis tier, Storage replication) with cost notes
- **1.1.4** [x] Draft IaC skeleton (Bicep or Terraform) modules and parameters with doxygen comments
- **1.1.5** [x] Add IaC lint/validate tasks and unit tests (naming, tags, locations)
- **1.1.6** [x] Add integration "plan/what-if" tests to assert expected resources
- **1.1.7** [x] Update `docs/planning/multi-agent-sync.md` notes during progress
- **1.1.8** [x] Acceptance review and finalize draft
- **1.1.T** [ ] Tests — unit, integration, acceptance for infra setup [ ] (est: 0.25d)
- **1.1.C** [ ] Commit and push your work: `git add -A && git commit -m "1.1: progress" && git push`

#### 1.2: Provision Azure resources [x] (est: 0.5d) ✅ **[COMPLETED: cascade-01 @2025-08-13T18:30:00-04:00] [feature/azure-provisioning]**

- **1.2.1** [x] Create resource group with proper naming and tags
- **1.2.2** [x] Provision Azure SQL Database with firewall rules (minimal public access, no VNET)
- **1.2.3** [x] Create Redis Cache instance with appropriate tier
- **1.2.4** [x] Set up Blob Storage with containers and access policies
- **1.2.5** [x] Create Key Vault with access policies and managed identity
- **1.2.6** [x] Create Application Insights instance for monitoring
- **1.2.T** [ ] Tests — unit, integration, acceptance for infra setup [ ] (est: 0.25d)
- **1.2.C** [ ] Commit and push your work: `git add -A && git commit -m "1.2: progress" && git push`

#### 1.3: Azure Functions setup [ ] (est: 0.5d)

- **1.3.2** [x] Create Function App with Python runtime ✅ **[COMPLETED: cascade-01 @2025-08-15T07:02:00-04:00] [feature/azure-functions-consumption-plan]**
- **1.3.3** [x] Configure app settings from Key Vault using managed identity ✅ **[COMPLETED: cascade-01 @2025-08-15T07:03:00-04:00] [feature/azure-functions-consumption-plan]**
- **1.3.4** [x] Set up connection strings and environment variables ✅ **[COMPLETED: cascade-01 @2025-08-15T07:03:30-04:00] [feature/azure-functions-consumption-plan]**
- **1.3.5** [x] Configure CORS and authentication settings ✅ **[COMPLETED: cascade-01 @2025-08-15T07:04:00-04:00] [feature/azure-functions-consumption-plan]**
- **1.3.T** [x] Tests — unit, integration, acceptance for infra setup ✅ **[COMPLETED: cascade-01 @2025-08-15T07:13:00-04:00] [feature/azure-functions-consumption-plan]** (est: 0.25d)
  - **1.3.C** [x] Commit and push your work: `git add -A && git commit -m "1.3: progress" && git push` ✅ **[COMPLETED: cascade-01 @2025-08-15T17:00:00-04:00] [agent-dev]**

#### 1.4: Repository and development environment [ ] (est: 0.25d)

- **1.4.1** [ ] Set up repository structure and branching strategy **[CHECKED OUT: cascade-01 @2025-08-15T17:00:00-04:00] [agent-dev] [CURRENT-TASK]**
  - Scope:
    - Define top-level repo structure: `frontend/`, `backend/`, `infrastructure/`, `tests/`, `docs/`, `scripts/`, `alembic/`.
    - Establish branching strategy: work on `agent-dev`; use `feature/*`, `fix/*`, `docs/*`, `chore/*`, `release/x.y.z`, `hotfix/*`.
    - Commit convention: `[Agent-ID] type(scope): description`.
    - PR policy: PRs target `agent-dev` with summary, scope, test results, coverage, affected files; link to plan tasks.
    - CI gates aligned with `Makefile`: `make lint`, `make test`, infra `make whatif` when infra changes; optional `make acceptance`.
    - Naming conventions: kebab-case (frontend paths), snake_case (Python), Bicep modules under `infrastructure/modules/`.
    - Protections: require PR + passing checks on `agent-dev`.
  - Acceptance Criteria:
    - `docs/planning/repository-structure.md` added with details (structure tree, branching, PR/CI rules, naming, protections).
    - This section reflects the same rules and references the new doc.
    - `make test` passes and documentation lint passes.
- **1.4.2** [ ] Configure development environment and dependencies
- **1.4.3** [ ] Create frontend scaffold with React/TypeScript/Tailwind
- **1.4.4** [ ] Set up development configuration files (.env, .gitignore, etc.)
- **1.4.5** [x] **Make targets for common workflows** ✅ **[COMPLETED: cascade-69 @2025-08-15T07:26:37-04:00]**
  - 1.4.5.1 [x] Add comprehensive test targets (unit, integration, acceptance, frontend, infra) ✅
  - 1.4.5.2 [x] Add linting targets (Python, JS/TS, Markdown) with auto-fix ✅
  - 1.4.5.3 [x] Add setup targets (backend, frontend, dev dependencies) ✅
  - 1.4.5.4 [x] Add development targets (preview, dev server, clean) ✅
  - 1.4.5.5 [x] Add deployment targets (infra, functions, full deploy) ✅

### **STANDARDIZED MAKE TARGETS - USE THESE FOR ALL WORKFLOWS**

**Testing (use instead of manual pytest/npm commands):**

- `make test` - Run all tests (unit + integration + acceptance)
- `make test-unit` - Run unit tests only
- `make test-integration` - Run integration tests
- `make test-acceptance` - Run acceptance tests (behave)
- `make test-frontend` - Run frontend tests (Jest/React Testing Library)
- `make test-infra` - Run infrastructure tests (Bicep validation)

**Development:**

- `make setup` - Complete project setup (backend + frontend + dev deps)
- `make preview` - Start dev servers (backend + frontend)
- `make dev` - Start development environment with hot reload
- `make clean` - Clean build artifacts and caches

**Code Quality:**

- `make lint` - Run all linters (Python, JS, Markdown)
- `make fix-lint` - Auto-fix linting issues where possible

**Deployment:**

- `make deploy` - Deploy full application (infra + functions)
- `make deploy-infra` - Deploy infrastructure only (Bicep)
- `make deploy-functions` - Deploy Azure Functions only
- **1.4.C** [ ] Commit and push your work: `git add -A && git commit -m "1.4: progress" && git push`
- **1.4.T** [ ] Tests — unit, integration, acceptance for infra setup [ ] (est: 0.25d)

#### 1.4.MY: Incremental mypy hardening for backend/ai/ [ ] (est: 0.25d)

- Goals: Re-enable strict typing gradually for `backend/ai/` without breaking CI.
- Approach: tighten per-module settings and address errors iteratively.
- Steps:
  - 1.4.MY.1 [ ] Enable `warn-unused-ignores`, `warn-redundant-casts` globally
  - 1.4.MY.2 [ ] For `backend/ai/base_provider.py`: set `disallow_untyped_defs = True`; fix signatures
  - 1.4.MY.3 [ ] For `backend/ai/config_manager.py`: add types for config shapes; enable `no_implicit_optional = True`
  - 1.4.MY.4 [ ] For `backend/ai/model_router.py`: add explicit `TypedDict`/`Protocol` for policies
  - 1.4.MY.5 [ ] For each provider (`grok_provider.py`, `openai_provider.py`, `claude_provider.py`, `local_provider.py`): add precise request/response DTOs
  - 1.4.MY.6 [ ] Remove `ignore_errors` for `backend/ai.*` package in `mypy.ini`, module-by-module
- Deliverables:
  - Updated `mypy.ini` with per-module overrides (dropping ignores as we fix types)
  - Type annotations and DTOs added to targeted modules
  - Tests passing (`make test`), mypy clean for modules in scope
- DoD:
  - mypy strict flags enabled for 3+ ai modules; 0 mypy errors for those modules
  - Coverage remains >85%; no regression in tests
- **1.4.MY.C** [ ] Commit and push your work: `git add -A && git commit -m "1.4.MY: mypy hardening progress" && git push`
- **1.4.MY.T** [ ] Tests — unit/integration on updated modules; mypy run clean [ ] (est: 0.1d)

#### 1.5: Static Web App configuration [x] (est: 0.25d)

- **1.5.1** [x] Create Azure Static Web App resource **[COMPLETED: cascade-01 @2025-08-15T07:20:30-04:00]**
  - 1.5.1.1 [x] Enhanced Static Web App Bicep module with API integration and authentication
  - 1.5.1.2 [x] Added GitHub repository integration and build configuration
  - 1.5.1.3 [x] Configured environment-specific SKU tiers (Free for dev/staging, Standard for prod)
  - 1.5.1.4 [x] Added comprehensive outputs for deployment automation
- **1.5.2** [x] Configure SWA to point API routes to Functions **[COMPLETED: cascade-01 @2025-08-15T07:20:30-04:00]**
  - 1.5.2.1 [x] Created staticwebapp.config.json with API routing configuration
  - 1.5.2.2 [x] Set up Azure Functions configuration files (host.json, function.json)
  - 1.5.2.3 [x] Configured CORS, security headers, and MIME types
  - 1.5.2.4 [x] Implemented role-based access control for API endpoints
- **1.5.3** [x] Set up custom domains and SSL certificates (if needed) **[COMPLETED: cascade-01 @2025-08-15T07:20:30-04:00]**
  - 1.5.3.1 [x] Created comprehensive custom domain setup documentation
  - 1.5.3.2 [x] Documented DNS configuration for CNAME and TXT records
  - 1.5.3.3 [x] Configured automatic SSL certificate management
  - 1.5.3.4 [x] Added environment-specific domain planning
- **1.5.4** [x] Configure authentication providers (Azure AD) **[COMPLETED: cascade-01 @2025-08-15T07:20:30-04:00]**
  - 1.5.4.1 [x] Created Azure AD authentication configuration documentation
  - 1.5.4.2 [x] Implemented frontend AuthService with TypeScript
  - 1.5.4.3 [x] Created backend authentication utilities for Azure Functions
  - 1.5.4.4 [x] Configured role-based access control and security decorators

- **1.5.T** [x] Tests — unit, integration, acceptance for infra setup [x] (est: 0.25d)
- **1.5.C** [x] Commit and push your work: `git add -A && git commit -m "1.5: Static Web App configuration complete" && git push` ✅ **[COMPLETED: cascade-01 @2025-08-15T17:06:54-04:00] [agent-dev]**

## 2: CI/CD and release-pack pipeline [ ] (est: 1 day)

### Definition of Done — Section 2 (CI/CD & Release)

- All workflows in `.github/workflows/` succeed on PR and main.
- Acceptance tests written using behave framework with Gherkin syntax for business-readable scenarios.
- Build artifacts (frontend, backend) produce deterministic outputs; cache configured.
- Release-pack artifacts generated on tag push and attached to GitHub Release.
- Manifest generated/validated; version and commit embedded.
- Secrets managed via GitHub Envs/Actions with no plaintext checked in.
- Docs updated: release process in `docs/deployment/azure-deployment-guide.md`.
- Planning updated: implementation plan and multi-agent sync.

  #2.1: SWA GitHub Actions deploy (tune `.github/workflows/azure-static-web-apps-*.yml`) [ ] (est: 0.25d) **[CHECKED OUT: cascade-69 @2025-08-15T08:25:01-04:00] [feature/swa-gha-deploy]**
      2.1.1 [ ] Configure SWA workflow with proper build commands and output directory
      2.1.2 [ ] Set up environment-specific deployment slots (staging/production)
      2.1.3 [ ] Configure secrets and environment variables in GitHub
      2.1.4 [ ] Test deployment pipeline with sample frontend changes
      2.1.T [ ] Tests — unit, integration, acceptance for infra setup [ ] (est: 0.25d)
      2.1.C [ ] Commit and push your work: `git add -A && git commit -m "2.1: progress" && git push`
  #2.2: Functions build/deploy workflow (Python) [ ] (est: 0.25d) **[CHECKED OUT: Sonnet-01 @2025-08-15T09:00:30-04:00] [feature/functions-gha-deploy]**
      2.2.1 [ ] Create GitHub Actions workflow for Azure Functions deployment
      2.2.2 [ ] Configure Python build steps with requirements installation
      2.2.3 [ ] Validate single-slot deployment on main
      2.2.4 [ ] Configure function app settings and connection strings
      2.2.T [ ] Tests — unit, integration, acceptance for infra setup [ ] (est: 0.25d)
      2.2.C [ ] Commit and push your work: `git add -A && git commit -m "2.2: progress" && git push`
  #2.3: On tag push: build release-pack (zip) + attach to GitHub Release [ ] (est: 0.25d) **[CHECKED OUT: cascade-03 @2025-08-15T16:51:37-04:00] [feature/release-pack]**
      2.3.1 [ ] Create release workflow triggered on tag creation
      2.3.2 [ ] Build and package all components (frontend, backend, docs)
      2.3.3 [ ] Generate release notes from commit history
      2.3.4 [ ] Attach release artifacts to GitHub Release
      2.3.T [ ] Tests — unit, integration, acceptance for infra setup [ ] (est: 0.25d)
      2.3.C [ ] Commit and push your work: `git add -A && git commit -m "2.3: progress" && git push`
  #2.4: Draft manifest.json spec (version, commit, API versions) [ ] (est: 0.25d)
      2.4.1 [ ] Define manifest schema with version, commit hash, and API versions
      2.4.2 [ ] Create build script to generate manifest during CI
      2.4.3 [ ] Include dependency versions and build metadata
      2.4.4 [ ] Validate manifest format and required fields
      2.4.T [ ] Tests — unit, integration, acceptance for infra setup [ ] (est: 0.25d)
      2.4.C [ ] Commit and push your work: `git add -A && git commit -m "2.4: progress" && git push`
  #2.T: Tests — unit, integration, acceptance for CI/CD + release-pack [ ] (est: 0.25d)
      2.T.C [ ] Commit and push your work: `git add -A && git commit -m "2.T: progress" && git push`

## 3: Chat interface (React/TS/Tailwind) [ ] (est: 2 days)

### Definition of Done — Section 3 (Frontend Chat)

- Unit tests for components/pages pass; `tsc` type-checks clean; ESLint/Prettier clean.
- Acceptance tests written using behave framework with Gherkin syntax for business-readable scenarios.
- Streaming UX implemented with retry/cancel; loading/error states covered.
- Accessibility: basic a11y checks (labels, contrast, tab order) for chat controls.
- Visuals: Cannasol branding applied; responsive on common breakpoints.
- API contracts mocked or integrated; no console errors at runtime.
- Docs updated: component structure and UX notes if applicable.
- Planning updated and test results reflected in plan/sync.
  #3.1: UI shell, routing, layout [x] (est: 0.25d) ✅ **[COMPLETED: cascade-02 @2025-01-15T11:00:00-05:00]**
      3.1.C [ ] Commit and push your work: `git add -A && git commit -m "3.1: progress" && git push`
      3.1.T [ ] Tests — unit, integration, acceptance for UI shell/routing [ ] (est: 0.1d)
  #3.2: Chat input, message list, timestamps [ ] (est: 0.5d) **[CHECKED OUT: cascade-02 @2025-08-15T16:47:12-04:00] [feature/chat-input-messages] [CURRENT-TASK]**
      3.2.1 [x] Implement `ChatInput` component ✅ **[COMPLETED: cascade-02 @2025-08-15T17:04:04-04:00]**
        - Autosize textarea; character limit warning; disabled during stream
        - Keyboard: Enter=send, Shift+Enter=newline, Cmd/Ctrl+Enter=send
      3.2.2 [ ] Implement `MessageList` item model
        - Sender styling (user/assistant/system), timestamp, status (streaming/complete/error)
        - Preserve partial content on cancel/error
      3.2.3 [ ] Wire to context/socket
        - Append outbound user message, start assistant placeholder on stream start
        - Update assistant message incrementally from SSE/socket events
      3.2.4 [ ] Accessibility & UX polish
        - Focus management after send/cancel; aria-live region for streaming
        - Loading/empty states and error toasts integration
      3.2.P [ ] Progress — 3.2.1 completed with autosize + char limit + a11y; assistant status set to 'sent' on stream end; added RTL unit tests; frontend suites passing (12/12, 44/44). **[cascade-02 @2025-08-15T17:04:04-04:00]**
      3.2.C [ ] Commit and push your work: `git add -A && git commit -m "3.2: progress" && git push`
      3.2.T [ ] Tests — unit, integration for chat input/message list [ ] (est: 0.2d)
        - RTL unit tests: input behaviors, keyboard shortcuts, disabled/limits
        - Integration: message append and streaming updates via mocked socket/client
  #3.3: Streaming display + retry/cancel [x] (est: 0.5d) ✅ **[COMPLETED: cascade-02 @2025-08-15T06:20:36-04:00] [feature/chat-streaming]**
      3.3.1 [x] Write unit tests: progressive chunk rendering (stream appends) ✅ **[COMPLETED: cascade-02 @2025-08-15T06:20:36-04:00]**
      3.3.2 [x] Write unit tests: Retry replays last prompt; Cancel aborts stream and preserves partial ✅ **[COMPLETED: cascade-02 @2025-08-15T06:20:36-04:00]**
      3.3.3 [x] Implement StreamRenderer component with Retry/Cancel controls ✅ **[COMPLETED: cascade-02 @2025-08-15T06:20:36-04:00]**
      3.3.4 [x] Client stream handler: fetch/SSE piping to state (mock backend if needed) ✅ **[COMPLETED: cascade-02 @2025-08-15T06:20:36-04:00]**
      3.3.T [x] All 3.3 tests passing (unit/integration) — update sync and test results tables ✅ **[COMPLETED: cascade-02 @2025-08-15T06:20:36-04:00]**
      3.3.C [ ] Commit and push your work: `git add -A && git commit -m "3.3: progress" && git push`
  #3.4: Error/loading states, toasts [x] (est: 0.25d) ✅ **[COMPLETED: cascade-02 @2025-08-15T06:50:00-04:00] [feature/chat-errors-toasts]**
      3.4.C [ ] Commit and push your work: `git add -A && git commit -m "3.4: progress" && git push`
      3.4.T [x] Tests — unit for error boundaries/loading/toasts ✅ **[COMPLETED: cascade-02 @2025-08-15T06:50:00-04:00]** (est: 0.15d)
  #3.5: Socket/client wiring for live updates [x] (est: 0.25d) ✅ **[COMPLETED: cascade-02 @2025-08-15T06:58:32-04:00] [feature/chat-sockets-live-updates]**
     3.5.C [ ] Commit and push your work: `git add -A && git commit -m "3.5: progress" && git push`
     3.5.T [x] Tests — integration for socket/client live updates ✅ **[COMPLETED: cascade-02 @2025-08-15T06:58:32-04:00]** (est: 0.2d)
  #3.6: Minimal admin panel shell (feature toggles) [x] (est: 0.25d) ✅ **[COMPLETED: cascade-02 @2025-08-15T07:16:56-04:00] [feature/admin-panel-shell]**
      3.6.C [ ] Commit and push your work: `git add -A && git commit -m "3.6: progress" && git push`
      3.6.T [x] Tests — unit for admin shell and toggles ✅ **[COMPLETED: cascade-02 @2025-08-15T07:16:56-04:00]** (est: 0.1d)
  #3.7: **REQUIRED** Cannasol logo integration [ ] (est: 0.15d)
      3.7.1 [x] Add Cannasol logo to header/navigation bar **[COMPLETED: cascade-01 @2025-08-15T06:08:35-04:00] [agent-dev]**
{{ ... }}
      3.7.2 [x] Integrate logo in chat interface branding **[COMPLETED: cascade-01 @2025-08-15T06:08:35-04:00]**
      3.7.3 [x] Add logo to loading states and splash screens **[COMPLETED: cascade-01 @2025-08-15T06:08:35-04:00]**
      3.7.4 [x] Ensure responsive logo display across devices **[COMPLETED: cascade-01 @2025-08-15T06:18:23-04:00] [agent-dev]**
      3.7.C [ ] Commit and push your work: `git add -A && git commit -m "3.7: progress" && git push`
      3.7.T [x] Tests — visual/regression checks for logo placement ✅ **[COMPLETED: cascade-02 @2025-08-15T07:17:32-04:00] [feature/admin-panel-shell]** (est: 0.05d)
  #3.8: Design system tokens + theming [ ] (est: 0.25d) **[CHECKED OUT: cascade-UI @2025-08-15T15:13:40-04:00] [agent-dev]**
      3.8.1 [ ] Establish Tailwind design tokens (colors, spacing, typography) aligned to Cannasol brand
      3.8.2 [ ] Implement CSS variables and Tailwind config for light/dark themes
      3.8.3 [ ] Add theme switcher with persisted preference (localStorage/System)
      3.8.4 [ ] Document tokens and usage in `frontend/README.md`
      3.8.T [ ] Tests — unit/snapshot for themed components; a11y contrast checks [ ] (est: 0.1d)
      3.8.C [ ] Commit and push your work: `git add -A && git commit -m "3.8: progress" && git push`
  #3.9: Chat UX polish (shortcuts, affordances, a11y) [ ] (est: 0.25d) **[CHECKED OUT: cascade-UI @2025-08-15T15:13:40-04:00] [agent-dev]**
      3.9.1 [ ] Cmd/Ctrl+Enter to send; Shift+Enter for newline; Esc to cancel stream
      3.9.2 [ ] Improve input states (disabled, loading, error) with clear affordances
      3.9.3 [ ] Enhance aria-live regions for streaming updates; focus management after send/cancel
      3.9.4 [ ] Add subtle animations/micro-interactions (reduced-motion safe)
      3.9.T [ ] Tests — RTL + a11y for keyboard/focus/aria-live behaviors [ ] (est: 0.1d)
      3.9.C [ ] Commit and push your work: `git add -A && git commit -m "3.9: progress" && git push`

## 4: GROK integration + model router stub [ ] (est: 1 day)

### Definition of Done — Section 4 (AI Providers & Router)

- Provider interfaces implemented with typed DTOs and error normalization.
- Acceptance tests written using behave framework with Gherkin syntax for business-readable scenarios.
- Model router routes by policy/env with tested fallbacks and timeouts.
- Rate limiting/backoff in place with deterministic tests.
- Secure config via env/Key Vault; no secrets in repo.
- Unit/integration tests cover provider stubs and routing policies; CI green.
- Docs updated for API and UI flows; planning updated.
  #4.1: Provider clients (GROK, placeholders for others) [x] (est: 0.25d) **[COMPLETED: augment-01 @2025-08-13T19:45:00-04:00]**
      - 4.1.1 [ ] Create base LLMProvider abstract class with standard interface
      - 4.1.2 [ ] Implement GROKProvider with API client and authentication
      - 4.1.3 [ ] Create placeholder providers for OpenAI, Claude, and local models
      - 4.1.4 [ ] Add provider configuration and credential management
      - 4.1.T [ ] Tests — unit/integration for provider clients [ ] (est: 0.15d)
      - 4.1.C [ ] Commit and push your work: `git add -A && git commit -m "4.1: progress" && git push`
  #4.2: ModelRouter.py (route by policy/env flag) [x] (est: 0.25d) — COMPLETED 2025-01-15
      - 4.2.1 [x] Design routing policy schema (cost, latency, capability-based) ✅ **[COMPLETED: cascade-03 @2025-08-15T06:30:00-04:00]**
      - 4.2.2 [x] Implement router logic with fallback mechanisms ✅ **[COMPLETED: cascade-03 @2025-08-15T06:20:15-04:00]**
      - 4.2.3 [x] Add environment-based provider selection ✅ **[COMPLETED: Sonnet-01 @2025-08-15T07:22:00-04:00]**
      - 4.2.4 [x] Create configuration interface for routing rules ✅ **[COMPLETED: Sonnet-01 @2025-08-15T07:22:00-04:00]**
      - 4.2.T [x] Tests — unit/integration for routing policies and env selection (est: 0.2d)
      - 4.2.C [ ] Commit and push your work: `git add -A && git commit -m "4.2: progress" && git push`
  #4.3: ContextManager.py (basic memory window) [x] (est: 0.25d) ✅ **[COMPLETED: Sonnet-01 @2025-08-15T07:05:23-04:00] [feature/context-manager]**
      - 4.3.1 [x] Design conversation context schema and storage ✅ **[COMPLETED: Sonnet-01 @2025-08-15T07:05:23-04:00]**
      - 4.3.2 [x] Implement sliding window memory management ✅ **[COMPLETED: Sonnet-01 @2025-08-15T07:05:23-04:00]**
      - 4.3.3 [x] Add context compression and summarization logic ✅ **[COMPLETED: Sonnet-01 @2025-08-15T07:05:23-04:00]**
      - 4.3.4 [x] Create context retrieval and injection mechanisms ✅ **[COMPLETED: Sonnet-01 @2025-08-15T07:05:23-04:00]**
      - 4.3.T [x] Tests — unit/integration for context management ✅ **[COMPLETED: Sonnet-01 @2025-08-15T07:05:23-04:00]** (est: 0.2d)
  #4.4: Rate limiting/backoff + error normalization [x] (est: 1d) — COMPLETED 2025-01-15
      - 4.4.1 [x] Implement token bucket rate limiting with configurable burst/refill
      - 4.4.2 [x] Add exponential backoff with jitter for retries
      - 4.4.3 [x] Create circuit breaker pattern for provider failures
      - 4.4.4 [x] Build error normalization layer for provider-specific errors
      - 4.4.T [x] Tests — unit/integration for rate limiting (est: 0.25d)
      - 4.4.C [ ] Commit and push your work: `git add -A && git commit -m "4.4: progress" && git push`
  #4.T: Tests — unit, integration, acceptance for model router [x] (est: 0.25d) ✅ **[COMPLETED: 2025-01-15]**
      - 4.T.1 [x] Write integration tests for model router
        - [x] Test multiple provider interactions
        - [x] Test fallback scenarios  
        - [x] Test configuration updates during runtime
      - 4.T.2 [x] Write acceptance tests for model router
        - [x] Test business scenarios and workflows
        - [x] Test environment-based deployments
        - [x] Test monitoring and observability
        - [x] Converted all pytest acceptance tests to `behave` with Gherkin scenarios.
      - 4.T.3 [x] Run comprehensive test suite
        - [x] Execute all unit, integration, and acceptance tests
        - [x] Verify test coverage and quality
        - [x] Fix any failing tests
      **Test Results Summary:**
      - Unit Tests: 22 tests passing
      - Integration Tests: 6 tests passing  
      - Acceptance Tests: 6 tests passing
      - Total Model Router Tests: 34 tests passing
      - Coverage: Comprehensive coverage of routing strategies, provider management, error handling, circuit breaker, rate limiting, and configuration interface

## 5: Task generation + approval skeleton [ ] (est: 2 days)

{{ ... }}

### Definition of Done — Section 5 (Tasking & Approvals)

- Intent detection rules tested; confidence/fallback behavior verified.
- Acceptance tests written using behave framework with Gherkin syntax for business-readable scenarios.
- Task schema and CRUD endpoints implemented with validation and pagination.
- Approval workflow state transitions covered by unit/integration tests.
- UI provides approve/reject with real-time status and preserves history.
- Audit logging present; permissions enforced where applicable.
- Docs updated for API and UI flows; planning updated.
  #5.1: Intent detection (rule-based MVP) [ ] (est: 0.5d) [CURRENT-TASK]
      - 5.1.1 [ ] Define task-generating intent categories (email, document, query, etc.) ✅ **[COMPLETED: cascade @2024-07-29T12:00:00-04:00]**
      - 5.1.2 [ ] Create rule-based classifier with keyword matching and patterns ✅ **[COMPLETED: cascade @2024-07-29T12:00:00-04:00]**
      - 5.1.3 [ ] Implement confidence scoring and fallback handling ✅ **[COMPLETED: cascade @2024-07-29T12:00:00-04:00]**
      - 5.1.4 [ ] Add intent validation and user confirmation prompts ✅ **[COMPLETED: cascade @2024-07-29T12:15:00-04:00]**
      - 5.1.T [ ] Tests — unit/integration for intent detection [ ] (est: 0.25d)
      - 5.1.C [ ] Commit and push your work: `git add -A && git commit -m "5.1: progress" && git push`
  #5.2: Task schema, DB table, CRUD endpoints [x] (est: 0.5d)
      - 5.2.1 [x] Design task database schema with status, metadata, and audit fields ✅ **[COMPLETED: cascade @2024-07-29T13:00:00-04:00]**
      - 5.2.2 [x] Create database migration scripts and indexes ✅ **[COMPLETED: cascade @2024-07-29T13:00:00-04:00]**
      - 5.2.3 [x] Implement CRUD API endpoints with validation and serialization ✅ **[COMPLETED: cascade @2024-07-29T13:00:00-04:00]**
      - 5.2.4 [x] Add task querying, filtering, and pagination support ✅ **[COMPLETED: cascade @2024-07-29T14:20:00-04:00]**
      - 5.2.4.1 [x] Add filtering by status ✅ **[COMPLETED: cascade @2024-07-29T13:30:00-04:00]**
      - 5.2.4.2 [x] Add filtering by date range ✅ **[COMPLETED: cascade @2024-07-29T14:00:00-04:00]**
      - 5.2.4.3 [x] Add free-text search on title/description ✅ **[COMPLETED: cascade @2024-07-29T14:15:00-04:00]**
      - 5.2.4.4 [x] Verify pagination (skip/limit) works with filters ✅ **[COMPLETED: cascade @2024-07-29T14:20:00-04:00]**
      - 5.2.T [x] Tests — unit/integration for task CRUD ✅ **[COMPLETED: cascade @2024-07-29T13:00:00-04:00]** (est: 0.2d)
      - 5.2.C [ ] Commit and push your work: `git add -A && git commit -m "5.2: progress" && git push`
  #5.3: ApprovalHandler.py (approve/reject) [x] (est: 0.5d) **[COMPLETED: cascade-01 @2025-08-15T08:11:00-04:00] [feature/approval-handler]**
      - 5.3.1 [x] Create approval workflow state machine
      - 5.3.2 [x] Implement approval/rejection logic with user context
      - 5.3.3 [x] Add approval notifications and status tracking
      - 5.3.4 [x] Create approval history and audit logging
      - 5.3.T [x] Tests — unit/integration for approval handling (est: 0.2d)
      - 5.3.C [ ] Commit and push your work: `git add -A && git commit -m "5.3: progress" && git push`
  #5.4: UI approve/reject buttons + status updates [ ] (est: 0.5d)
      - 5.4.1 [x] Design task approval interface with clear action buttons ✅ **[COMPLETED: cascade-01 @2025-08-15T16:02:29-04:00] [feature/approve-reject-ui]**
      - 5.4.2 [x] Implement real-time status updates and notifications ✅ **[COMPLETED: cascade-01 @2025-08-15T16:02:29-04:00] [feature/approve-reject-ui]**
      - 5.4.3 [x] Add task details view with approval history ✅ **[COMPLETED: cascade-01 @2025-08-15T09:00:00-04:00]**
      - 5.4.4 [ ] Create bulk approval functionality for multiple tasks
      - 5.4.T [x] Tests — UI integration for approvals/status updates ✅ **[COMPLETED: cascade-01 @2025-08-15T16:02:29-04:00] [feature/approve-reject-ui]** (est: 0.2d)
      - 5.4.C [ ] Commit and push your work: `git add -A && git commit -m "5.4: progress" && git push`
  #5.T: Tests — unit, integration, acceptance for tasking [ ] (est: 0.5d)

## 6: Inventory integration [ ] (est: 2 days)

### Definition of Done — Section 6 (Inventory)

- Client with typed models; retries/backoff and error handling covered by tests.
- Acceptance tests written using behave framework with Gherkin syntax for business-readable scenarios.
- Read endpoints support filtering/sorting/pagination; write endpoints validate inputs.
- Basic UI list/detail flows work; empty/loading/error states covered.
- Caching (if added) validated; no PII leakage; telemetry optional and privacy-safe.
- Docs updated for endpoints and UI; planning updated.
  #6.1: InventoryClient.py with typed DTOs [ ] (est: 0.5d)
      - 6.1.1 [ ] Define inventory data models and DTOs with type annotations
      - 6.1.2 [ ] Create inventory client with connection management and retry logic
      - 6.1.3 [ ] Implement data serialization and deserialization
      - 6.1.4 [ ] Add client configuration and credential management
      - 6.1.T [ ] Tests — unit for client and model DTOs [ ] (est: 0.2d)
      - 6.1.C [ ] Commit and push your work: `git add -A && git commit -m "6.1: progress" && git push`
  #6.2: Read endpoints (list/filter) + pagination [ ] (est: 0.5d)
      - 6.2.1 [ ] Implement inventory listing with sorting and filtering
      - 6.2.2 [ ] Add pagination support with cursor-based or offset pagination
      - 6.2.3 [ ] Create search functionality with full-text and field-specific search
      - 6.2.4 [ ] Add caching layer for frequently accessed inventory data
      - 6.2.T [ ] Tests — integration for read endpoints [ ] (est: 0.2d)
      - 6.2.C [ ] Commit and push your work: `git add -A && git commit -m "6.2: progress" && git push`
  #6.3: Write endpoints (create/update) + validation [ ] (est: 0.5d)
      - 6.3.1 [ ] Implement inventory item creation with validation rules
      - 6.3.2 [ ] Add inventory update functionality with conflict resolution
      - 6.3.3 [ ] Create batch operations for bulk inventory changes
      - 6.3.4 [ ] Add inventory change tracking and audit logging
      - 6.3.T [ ] Tests — integration for write endpoints [ ] (est: 0.2d)
      - 6.3.C [ ] Commit and push your work: `git add -A && git commit -m "6.3: progress" && git push`
  #6.4: UI inventory viewer (basic) [ ] (est: 0.5d)
      - 6.4.1 [ ] Create inventory list view with search and filter controls
      - 6.4.2 [ ] Implement inventory item detail view and editing forms
      - 6.4.3 [ ] Add inventory data visualization (charts, summaries)
      - 6.4.4 [ ] Create inventory export functionality (CSV, Excel)
      - 6.4.T [ ] Tests — UI integration for inventory views [ ] (est: 0.2d)
      - 6.4.C [ ] Commit and push your work: `git add -A && git commit -m "6.4: progress" && git push`
  #6.T: Tests — unit, integration, acceptance for inventory [ ] (est: 0.5d)

## 7: NL→SQL (inventory-only, whitelisted) [ ] (est: 1 day)

### Definition of Done — Section 7 (NL→SQL)

- Only whitelisted templates executable; params validated; injection-safe.
- Acceptance tests written using behave framework with Gherkin syntax for business-readable scenarios.
- Intent mapping and param extraction tested with representative phrases.
- Execution layer enforces limits (row caps, timeouts, RBAC) with tests.
- Results formatted deterministically; audit trail recorded.
- Docs updated for templates and guardrails; planning updated.
  #7.1: QueryTemplates.py (whitelist + param schema) [ ] (est: 0.25d)
      - 7.1.1 [ ] Define inventory query templates (list, search, filter, aggregate)
      - 7.1.2 [ ] Create parameter schema with validation rules
      - 7.1.3 [ ] Implement template registry with metadata
      - 7.1.4 [ ] Add template versioning and deprecation support
      - 7.1.T [ ] Tests — unit for templates and param schema [ ] (est: 0.15d)
      - 7.1.C [ ] Commit and push your work: `git add -A && git commit -m "7.1: progress" && git push`
  #7.2: IntentDetector.py (map to template) [ ] (est: 0.25d)
      - 7.2.1 [ ] Create rule-based intent classification for inventory queries
      - 7.2.2 [ ] Implement parameter extraction from natural language
      - 7.2.3 [ ] Add confidence scoring for intent matches
      - 7.2.4 [ ] Create fallback handling for unrecognized intents
      - 7.2.T [ ] Tests — unit/integration for intent mapping [ ] (est: 0.15d)
      - 7.2.C [ ] Commit and push your work: `git add -A && git commit -m "7.2: progress" && git push`
  #7.3: Executor.py (parameterized exec + limits) [ ] (est: 0.25d)
      - 7.3.1 [ ] Implement safe SQL execution with parameter binding
      - 7.3.2 [ ] Add query result formatting and serialization
      - 7.3.3 [ ] Create execution context with user permissions
      - 7.3.4 [ ] Add query logging and audit trail
      - 7.3.T [ ] Tests — integration for executor + limits [ ] (est: 0.15d)
      - 7.3.C [ ] Commit and push your work: `git add -A && git commit -m "7.3: progress" && git push`

## 8: Email integration (Microsoft Exchange) [ ] (est: 1 day)

### Definition of Done — Section 8 (Email - Exchange)

- Graph client/auth configured; no secrets committed; permissions verified in dev.
- Acceptance tests written using behave framework with Gherkin syntax for business-readable scenarios.
- Summarize/draft/send endpoints implemented with approval gating.
- Attachments/calendar behaviors covered where in scope; errors handled.
- UI hooks present with confirmations and toasts.
- Tests pass for wrapper and end-to-end happy path; docs/planning updated.
  #8.1: Email summarize/draft/send [ ] (est: 0.5d)
      - 8.1.1 [ ] Implement email summarization endpoint (Graph API)
      - 8.1.2 [ ] Draft response generation with approval workflow
      - 8.1.3 [ ] Send email with priority, CC/BCC, and audit logging
      - 8.1.C [ ] Commit and push your work: `git add -A && git commit -m "8.1: progress" && git push`
  #8.2: Attachments and calendar [ ] (est: 0.25d)
      - 8.2.1 [ ] Attachment handling (upload/download, size limits)
      - 8.2.2 [ ] Calendar integration for meeting requests (create/invite)
      - 8.2.3 [ ] Error handling and permission checks
      - 8.2.C [ ] Commit and push your work: `git add -A && git commit -m "8.2: progress" && git push`
  #8.3: UI hooks [ ] (est: 0.15d)
      - 8.3.1 [ ] Chat actions: “Summarize”, “Draft”, “Send”
      - 8.3.2 [ ] Approval modal and status toasts
      - 8.3.C [ ] Commit and push your work: `git add -A && git commit -m "8.3: progress" && git push`
  #8.T: Tests — unit/integration for email [ ] (est: 0.1d)
      - 8.T.1 [ ] Unit tests for Graph client wrappers
      - 8.T.2 [ ] Integration tests for summarize/draft/send flow

## 9: Document management (templates) [ ] (est: 1 day)

### Definition of Done — Section 9 (Documents - Templates)

- Versioned template store with validation; metadata persisted.
- Acceptance tests written using behave framework with Gherkin syntax for business-readable scenarios.
- Generation endpoints produce expected outputs; preview/download working.
- Multi-format export validated where in scope; errors handled.
- UI flows for generate/preview integrated; tests pass; docs/planning updated.
  #9.1: Template store + validation [ ] (est: 0.5d)
      - 9.1.1 [ ] Template repository in Blob (versioned)
      - 9.1.2 [ ] Field validation and constraints
      - 9.1.3 [ ] Multi-format export (PDF/DOCX/XLSX)
      - 9.1.C [ ] Commit and push your work: `git add -A && git commit -m "9.1: progress" && git push`
  #9.2: Generation endpoints [ ] (est: 0.25d)
      - 9.2.1 [ ] Generate from template with data mapping
      - 9.2.2 [ ] Download/preview endpoints
      - 9.2.C [ ] Commit and push your work: `git add -A && git commit -m "9.2: progress" && git push`
  #9.3: UI hooks [ ] (est: 0.15d)
      - 9.3.1 [ ] “Generate Document” action with form input
      - 9.3.2 [ ] Result preview and download
      - 9.3.C [ ] Commit and push your work: `git add -A && git commit -m "9.3: progress" && git push`
  #9.T: Tests — unit/integration for documents [ ] (est: 0.1d)
      - 9.T.1 [ ] Unit tests for template validation
      - 9.T.2 [ ] Integration tests for generation + download

  #7.4: Guardrails: row limits, timeouts, RBAC check [ ] (est: 0.25d)
      - 7.4.1 [ ] Implement row count limits and pagination
      - 7.4.2 [ ] Add query timeout and resource limits
      - 7.4.3 [ ] Create RBAC checks for data access permissions
      - 7.4.4 [ ] Add SQL injection prevention and validation
  #7.T: Tests — unit, integration, acceptance for NL→SQL [ ] (est: 0.25d)

## 8: Email integration (Microsoft 365) [ ] (est: 1 day)

  #8.1: Microsoft Graph client setup [ ] (est: 0.25d)
      - 8.1.1 [ ] Register application in Azure AD with required permissions
      - 8.1.2 [ ] Configure Microsoft Graph SDK and authentication
      - 8.1.3 [ ] Set up service principal or managed identity for Graph access
      - 8.1.4 [ ] Test basic Graph API connectivity and permissions
      - 8.1.C [ ] Commit and push your work: `git add -A && git commit -m "8.1: progress" && git push`
  #8.2: Send mail endpoint + template support [ ] (est: 0.5d)
      - 8.2.1 [ ] Create email template system with variable substitution
      - 8.2.2 [ ] Implement send mail function with attachment support
      - 8.2.3 [ ] Add email validation and sanitization
      - 8.2.4 [ ] Create email queue and retry mechanism for failures
      - 8.2.C [ ] Commit and push your work: `git add -A && git commit -m "8.2: progress" && git push`
  #8.3: Basic UI action to trigger email [ ] (est: 0.25d)
      - 8.3.1 [ ] Add email composition interface in admin panel
      - 8.3.2 [ ] Create email preview functionality
      - 8.3.3 [ ] Implement send confirmation and status tracking
      8.3.4 [ ] Add email history and delivery status view
      - 8.3.C [ ] Commit and push your work: `git add -A && git commit -m "8.3: progress" && git push`
  #8.T: Tests — unit, integration, acceptance for email [ ] (est: 0.25d)

## 9: Document generation (PDF/DOCX) [ ] (est: 1 day)

### Definition of Done — Section 9 (Documents - Generation)

- Template schema defined; upload/validation implemented.
- Acceptance tests written using behave framework with Gherkin syntax for business-readable scenarios.
- DOCX merge and PDF export produce deterministic outputs in tests.
- Queue/pipeline logic (if implemented) has retry/backoff and logging.
- Secure download links with expiration; versioning/history tracked.
- Tests pass; docs/planning updated.
  #9.1: Template storage (Blob) + metadata in SQL [ ] (est: 0.25d)
      - 9.1.1 [ ] Design document template schema and metadata structure
      - 9.1.2 [ ] Create blob storage containers for templates and generated docs
      - 9.1.3 [ ] Implement template upload and validation functionality
      - 9.1.4 [ ] Add template versioning and approval workflow
      - 9.1.C [ ] Commit and push your work: `git add -A && git commit -m "9.1: progress" && git push`
  #9.2: DOCX template merge and PDF export [ ] (est: 0.5d)
      - 9.2.1 [ ] Integrate python-docx for DOCX template processing
      - 9.2.2 [ ] Implement variable substitution and conditional content
      - 9.2.3 [ ] Add PDF conversion using LibreOffice or similar
      - 9.2.4 [ ] Create document generation queue and processing pipeline
      - 9.2.C [ ] Commit and push your work: `git add -A && git commit -m "9.2: progress" && git push`
  #9.3: Download link + versioning [ ] (est: 0.25d)
      - 9.3.1 [ ] Generate secure download links with expiration
      - 9.3.2 [ ] Implement document versioning and history tracking
      - 9.3.3 [ ] Add document access logging and permissions
      - 9.3.4 [ ] Create document management UI for admins
      - 9.3.C [ ] Commit and push your work: `git add -A && git commit -m "9.3: progress" && git push`
  #9.T: Tests — unit, integration, acceptance for document generation [ ] (est: 0.25d)

## 10: Auth (Azure AD SSO) + RBAC [ ] (est: 1 day)

### Definition of Done — Section 10 (Auth & RBAC)

- Frontend MSAL login/logout flows work; tokens stored securely.
- Acceptance tests written using behave framework with Gherkin syntax for business-readable scenarios.
- Backend JWT validation and authorization middleware enforced.
- Roles/permissions seeded; checks covered by unit/integration tests.
- Admin view shows permissions; audit logs recorded where applicable.
- Security review complete; docs/planning updated.
  #10.1: Frontend MSAL setup + login flow [ ] (est: 0.25d)
      - 10.1.1 [ ] Configure MSAL library with Azure AD app registration
      - 10.1.2 [ ] Implement login/logout components and routing guards
      - 10.1.3 [ ] Add token refresh and silent authentication
      - 10.1.4 [ ] Create user profile display and session management
      - 10.1.C [ ] Commit and push your work: `git add -A && git commit -m "10.1: progress" && git push`
  #10.2: Backend token validation middleware [ ] (est: 0.25d)
      - 10.2.1 [ ] Implement JWT token validation middleware
      - 10.2.2 [ ] Add Azure AD token verification and claims extraction
      - 10.2.3 [ ] Create user context and session management
      - 10.2.4 [ ] Add API endpoint protection and authorization
      - 10.2.C [ ] Commit and push your work: `git add -A && git commit -m "10.2: progress" && git push`
  #10.3: Users/Permissions tables seeding + role checks [ ] (est: 0.25d)
      - 10.3.1 [ ] Design user, role, and permission database schema
      - 10.3.2 [ ] Create database migration scripts and seed data
      - 10.3.3 [ ] Implement role-based access control logic
      - 10.3.4 [ ] Add permission checking decorators and middleware
      - 10.3.C [ ] Commit and push your work: `git add -A && git commit -m "10.3: progress" && git push`
  #10.4: Permission matrix in UI (read-only MVP) [ ] (est: 0.25d)
      - 10.4.1 [ ] Create admin interface for viewing user permissions
      - 10.4.2 [ ] Implement role assignment and management UI
      - 10.4.3 [ ] Add permission audit trail and logging
      - 10.4.4 [ ] Create user access reports and analytics
      - 10.4.C [ ] Commit and push your work: `git add -A && git commit -m "10.4: progress" && git push`
  #10.T: Tests — unit, integration, acceptance for auth [ ] (est: 0.25d)

## 11: Telemetry/analytics (privacy-safe) [ ] (est: 1 day)

### Definition of Done — Section 11 (Telemetry)

- DDL created with indexes; retention policies documented.
- Acceptance tests written using behave framework with Gherkin syntax for business-readable scenarios.
- Instrumentation records latency, errors, token usage with redaction/anonymization.
- Configurable sampling flags default to privacy-safe off.
- Admin metrics view shows key KPIs; tests pass; docs/planning updated.
  #11.1: DDL for Analytics_* tables [ ] (est: 0.25d)
      - 11.1.1 [ ] Design analytics database schema (events, metrics, sessions)
      - 11.1.2 [ ] Create partitioned tables for time-series data
      - 11.1.3 [ ] Add indexes and constraints for query performance
      - 11.1.4 [ ] Implement data retention and archival policies
      - 11.1.C [ ] Commit and push your work: `git add -A && git commit -m "11.1: progress" && git push`
  #11.2: Telemetry instrumentation (latency, tokens, errors) [ ] (est: 0.25d)
      - 11.2.1 [ ] Add performance monitoring and latency tracking
      - 11.2.2 [ ] Implement token usage and cost tracking
      - 11.2.3 [ ] Create error tracking and categorization
      - 11.2.4 [ ] Add custom metrics and business KPIs
      - 11.2.C [ ] Commit and push your work: `git add -A && git commit -m "11.2: progress" && git push`
  #11.3: Redaction pipeline + config flag; sampling off by default [ ] (est: 0.25d)
      - 11.3.1 [ ] Implement PII detection and redaction pipeline
      - 11.3.2 [ ] Add configurable sampling rates and privacy controls
      - 11.3.3 [ ] Create data anonymization and aggregation rules
      - 11.3.4 [ ] Add consent management and opt-out mechanisms
      - 11.3.C [ ] Commit and push your work: `git add -A && git commit -m "11.3: progress" && git push`
  #11.4: Admin metrics view (p95, error rate) [ ] (est: 0.25d)
      - 11.4.1 [ ] Create real-time dashboard with key metrics
      - 11.4.2 [ ] Implement alerting for error rates and performance
      - 11.4.3 [ ] Add historical trend analysis and reporting
      - 11.4.4 [ ] Create exportable reports and data visualization
      - 11.4.C [ ] Commit and push your work: `git add -A && git commit -m "11.4: progress" && git push`
  #11.T: Tests — unit, integration, acceptance for telemetry/analytics [ ] (est: 0.25d)

## 12: Release-pack deliverable [ ] (est: 0.5 day)

### Definition of Done — Section 12 (Release Pack)

- Manifest and API schema generated and validated.
- Acceptance tests written using behave framework with Gherkin syntax for business-readable scenarios.
- Release includes app, migrations, analytics schema, and deployment config.
- Installation/upgrade docs generated; reproducible build verified in CI.
- Tests for packaging pass; planning updated.
- **#12.1: Define manifest.json + api-schema.json (OpenAPI export) [ ] (est: 0.25d)**
  - 12.1.1 [ ] Create comprehensive manifest schema with all metadata
  - 12.1.2 [ ] Generate OpenAPI specification from API endpoints
  - 12.1.3 [ ] Add API versioning and compatibility information
  - 12.1.4 [ ] Include dependency versions and system requirements
  - 12.1.C [ ] Commit and push your work: `git add -A && git commit -m "12.1: progress" && git push`
- **#12.2: Pack db migrations + analytics-schema.json + deployment.json [ ] (est: 0.25d)**
  - 12.2.1 [ ] Package all database migration scripts and schemas
  - 12.2.2 [ ] Create deployment configuration templates
  - 12.2.3 [ ] Add environment-specific configuration examples
  - 12.2.4 [ ] Generate installation and upgrade documentation
  - 12.2.C [ ] Commit and push your work: `git add -A && git commit -m "12.2: progress" && git push`
- **#12.T: Tests — unit, integration, acceptance for release-pack [ ] (est: 0.25d)**

## 13: Testing + deployment [ ] (est: 2 days)

### Definition of Done — Section 13 (Testing & Deployment)

- Unit, integration, acceptance tests implemented per sections and all green in CI.
- Acceptance tests written using behave framework with Gherkin syntax for business-readable scenarios.
- Performance tests meet PRD thresholds; report attached to PR/Release.
- E2E happy path verified; non-flaky CI runs over multiple commits.
- Deployment steps documented and validated in dev; planning updated.
  - **#13.1: Unit tests: router, tasking, NL→SQL templates [ ] (est: 0.75d)**
  - 13.1.C [ ] Commit and push your work: `git add -A && git commit -m "13.1: progress" && git push`
  - **#13.2: Integration tests: Functions endpoints + SQL [ ] (est: 0.5d)**
  - 13.2.C [ ] Commit and push your work: `git add -A && git commit -m "13.2: progress" && git push`
  - **#13.3: E2E happy path (chat → task → inventory → doc/email) [ ] (est: 0.5d)**
  - 13.3.C [ ] Commit and push your work: `git add -A && git commit -m "13.3: progress" && git push`
  - **#13.4: Performance tests (k6/Locust) with PRD thresholds [ ] (est: 0.25d)**
    - 13.4.1 [ ] Simple queries p95 < 2s; single integration p95 < 5s; multi-system p95 < 10s
    - 13.4.2 [ ] 20 concurrent users; 1000 req/hour sustained; graceful degradation verified
    - 13.4.C [ ] Commit and push your work: `git add -A && git commit -m "13.4: progress" && git push`
  - **#13.5: Acceptance tests (pytest-bdd/behave) mapped to PRD scenarios [ ] (est: 0.5d)**
  - 13.5.C [ ] Commit and push your work: `git add -A && git commit -m "13.5: progress" && git push`

---

Note: Remember to update this plan after each completed task or subtask by:

  1. Checking off [ ] to [x].
  2. Removing [CURRENT-TASK] from the completed item.
  3. Adding [CURRENT-TASK] to the next active task or subtask.
