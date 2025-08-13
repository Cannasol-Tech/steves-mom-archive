# Implementation Plan: Steve's Mom AI Chatbot (MVP)

This plan follows the 2-week MVP timeline from PRD section 18.1 and your DoD: each section must conclude with 100% passing unit, integration, and acceptance tests (pytest/behave) mapped to PRD requirements in `docs/prd-v1.0.0`.

Current constraints/choices:
- Azure Functions on Consumption (or Flex Consumption On‑Demand with 0 Always Ready) for lowest cost; avoid Premium for MVP.
- NL→SQL limited to Inventory only using whitelisted query templates and guardrails.
- Privacy‑safe telemetry by default (no raw content retained; sampling disabled by default).
- Publish a release‑pack consumable by `functionality-reports` (spec TBD; placeholder implemented in MVP).

## Current Task Tagging
Current Task Tagging: Tag the task/subtask you are actively working on with [CURRENT-TASK]. Always move this tag to the next active item once the current one is complete.

---

#1: Infrastructure setup (Consumption plan) [ ] (est: 2 days) [CURRENT-TASK]
  #1.1: Azure resources IaC draft (naming, SKUs) [ ] (est: 0.25d)
  #1.2: Provision Azure SQL, Redis, Blob, Key Vault [ ] (est: 0.5d)
  #1.3: Configure SQL firewall, minimal public access (no VNET) [ ] (est: 0.25d)
  #1.4: Create Functions Consumption plan + Function App [ ] (est: 0.25d)
  #1.5: Configure app settings from Key Vault (managed identity) [ ] (est: 0.25d)
  #1.6: Base repo structure + Python env + frontend scaffold [ ] (est: 0.25d)
  #1.7: SWA config to point API to Functions [ ] (est: 0.25d)
  #1.T: Tests — unit, integration, acceptance for infra setup [ ] (est: 0.25d)

#2: CI/CD and release-pack pipeline [ ] (est: 1 day)
  #2.1: SWA GitHub Actions deploy (tune `.github/workflows/azure-static-web-apps-*.yml`) [ ] (est: 0.25d)
  #2.2: Functions build/deploy workflow (Python) [ ] (est: 0.25d)
  #2.3: On tag push: build release-pack (zip) + attach to GitHub Release [ ] (est: 0.25d)
  #2.4: Draft manifest.json spec (version, commit, API versions) [ ] (est: 0.25d)
  #2.T: Tests — unit, integration, acceptance for CI/CD + release-pack [ ] (est: 0.25d)

#3: Chat interface (React/TS/Tailwind) [ ] (est: 2 days)
  #3.1: UI shell, routing, layout [ ] (est: 0.25d)
  #3.2: Chat input, message list, timestamps [ ] (est: 0.5d)
  #3.3: Streaming display + retry/cancel [ ] (est: 0.5d)
  #3.4: Error/loading states, toasts [ ] (est: 0.25d)
  #3.5: Socket/client wiring for live updates [ ] (est: 0.25d)
  #3.6: Minimal admin panel shell (feature toggles) [ ] (est: 0.25d)
  #3.T: Tests — unit (components), integration (API/socket), acceptance (chat flow) [ ] (est: 0.25d)

#4: GROK integration + model router stub [ ] (est: 1 day)
  #4.1: Provider clients (GROK, placeholders for others) [ ] (est: 0.25d)
  #4.2: ModelRouter.py (route by policy/env flag) [ ] (est: 0.25d)
  #4.3: ContextManager.py (basic memory window) [ ] (est: 0.25d)
  #4.4: Rate limiting/backoff + error normalization [ ] (est: 0.25d)
  #4.T: Tests — unit, integration, acceptance for model router [ ] (est: 0.25d)

#5: Task generation + approval skeleton [ ] (est: 2 days)
  #5.1: Intent detection (rule-based MVP) [ ] (est: 0.5d)
  #5.2: Task schema, DB table, CRUD endpoints [ ] (est: 0.5d)
  #5.3: ApprovalHandler.py (approve/reject) [ ] (est: 0.5d)
  #5.4: UI approve/reject buttons + status updates [ ] (est: 0.5d)
  #5.T: Tests — unit, integration, acceptance for tasking [ ] (est: 0.5d)

#6: Inventory integration [ ] (est: 2 days)
  #6.1: InventoryClient.py with typed DTOs [ ] (est: 0.5d)
  #6.2: Read endpoints (list/filter) + pagination [ ] (est: 0.5d)
  #6.3: Write endpoints (create/update) + validation [ ] (est: 0.5d)
  #6.4: UI inventory viewer (basic) [ ] (est: 0.5d)
  #6.T: Tests — unit, integration, acceptance for inventory [ ] (est: 0.5d)

#7: NL→SQL (inventory-only, whitelisted) [ ] (est: 1 day)
  #7.1: QueryTemplates.py (whitelist + param schema) [ ] (est: 0.25d)
  #7.2: IntentDetector.py (map to template) [ ] (est: 0.25d)
  #7.3: Executor.py (parameterized exec + limits) [ ] (est: 0.25d)
  #7.4: Guardrails: row limits, timeouts, RBAC check [ ] (est: 0.25d)
  #7.T: Tests — unit, integration, acceptance for NL→SQL [ ] (est: 0.25d)

#8: Email integration (Microsoft 365) [ ] (est: 1 day)
  #8.1: Microsoft Graph client setup [ ] (est: 0.25d)
  #8.2: Send mail endpoint + template support [ ] (est: 0.5d)
  #8.3: Basic UI action to trigger email [ ] (est: 0.25d)
  #8.T: Tests — unit, integration, acceptance for email [ ] (est: 0.25d)

#9: Document generation (PDF/DOCX) [ ] (est: 1 day)
  #9.1: Template storage (Blob) + metadata in SQL [ ] (est: 0.25d)
  #9.2: DOCX template merge and PDF export [ ] (est: 0.5d)
  #9.3: Download link + versioning [ ] (est: 0.25d)
  #9.T: Tests — unit, integration, acceptance for document generation [ ] (est: 0.25d)

#10: Auth (Azure AD SSO) + RBAC [ ] (est: 1 day)
  #10.1: Frontend MSAL setup + login flow [ ] (est: 0.25d)
  #10.2: Backend token validation middleware [ ] (est: 0.25d)
  #10.3: Users/Permissions tables seeding + role checks [ ] (est: 0.25d)
  #10.4: Permission matrix in UI (read-only MVP) [ ] (est: 0.25d)
  #10.T: Tests — unit, integration, acceptance for auth [ ] (est: 0.25d)

#11: Telemetry/analytics (privacy-safe) [ ] (est: 1 day)
  #11.1: DDL for Analytics_* tables [ ] (est: 0.25d)
  #11.2: Telemetry instrumentation (latency, tokens, errors) [ ] (est: 0.25d)
  #11.3: Redaction pipeline + config flag; sampling off by default [ ] (est: 0.25d)
  #11.4: Admin metrics view (p95, error rate) [ ] (est: 0.25d)
  #11.T: Tests — unit, integration, acceptance for telemetry/analytics [ ] (est: 0.25d)

#12: Release-pack deliverable [ ] (est: 0.5 day)
  #12.1: Define manifest.json + api-schema.json (OpenAPI export) [ ] (est: 0.25d)
  #12.2: Pack db migrations + analytics-schema.json + deployment.json [ ] (est: 0.25d)
  #12.T: Tests — unit, integration, acceptance for release-pack [ ] (est: 0.25d)

#13: Testing + deployment [ ] (est: 2 days)
  #13.1: Unit tests: router, tasking, NL→SQL templates [ ] (est: 0.75d)
  #13.2: Integration tests: Functions endpoints + SQL [ ] (est: 0.5d)
  #13.3: E2E happy path (chat → task → inventory → doc/email) [ ] (est: 0.5d)
  #13.4: Load sanity (light k6 or Locust) + final deploy [ ] (est: 0.25d)
  #13.5: Acceptance tests (pytest-bdd/behave) mapped to PRD scenarios [ ] (est: 0.5d)

---

Note: Remember to update this plan after each completed task or subtask by:
  1. Checking off [ ] to [x].
  2. Removing [CURRENT-TASK] from the completed item.
  3. Adding [CURRENT-TASK] to the next active task or subtask.
