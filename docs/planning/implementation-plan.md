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

- **Active Agent:** Cascade-69 (registered 2025-08-13T21:54:57-04:00)

- **Checkout format:**

```markdown
- [ ] Task description **[CHECKED OUT: Cascade-69 @YYYY-MM-DDThh:mm:ss-04:00] [feature/descriptive-branch]**
```

### Test Results (append entries as tasks complete)

| Task ID | Agent | Unit Tests | Integration Tests | Acceptance Tests | Coverage |
|---------|-------|------------|-------------------|------------------|----------|

### Completed Tasks

| Task ID | Agent | Branch | Duration | Files Modified | Merged |
|---------|-------|--------|----------|----------------|--------|
| 4.1 | augment-01 | feature/ai-provider-clients | 45min | 7 files | ✅ |

### Communication Log

| Timestamp | From | To | Message | Action Required |
|-----------|------|----|---------|-----------------|
| 2025-08-13T19:45:00-04:00 | augment-01 | ALL | Task 4.1 complete: Built comprehensive AI provider abstraction layer with GROK provider and placeholders for OpenAI, Claude, and Local models. Includes configuration management, credential handling, and provider fallback system. All tests passing. | Ready for integration with existing AI agent |

### Implementation Plan

## 1: Infrastructure setup (Consumption plan) [ ] (est: 2 days)

> Hosting note: Using Azure Functions Consumption (or Flex On‑Demand) for MVP to minimize cost. PRD Appendix mentions Functions Premium; evaluate upgrade after MVP acceptance.

  #1.1: Azure resources IaC draft (naming, SKUs) [x] (est: 0.5d) ✅ **[COMPLETED: cascade-01 @2025-08-13T17:45:00-04:00] [feature/infrastructure-iac-draft]**
      1.1.1 [x] Define TDD scope for IaC: write test plan for naming rules and SKU validation (unit/integration)
      1.1.2 [x] Establish naming conventions (resource group, functions, storage, sql, redis, kv) with examples and doc in `docs/architecture/naming.md`
      1.1.3 [x] Select SKUs for each service (Functions Consumption/Flex, SQL tier, Redis tier, Storage replication) with cost notes
      1.1.4 [x] Draft IaC skeleton (Bicep or Terraform) modules and parameters with doxygen comments
      1.1.5 [x] Add IaC lint/validate tasks and unit tests (naming, tags, locations)
      1.1.6 [x] Add integration "plan/what-if" tests to assert expected resources
      1.1.7 [x] Update `docs/planning/multi-agent-sync.md` notes during progress
      1.1.8 [x] Acceptance review and finalize draft
  #1.2: Provision Azure resources [x] (est: 0.5d) ✅ **[COMPLETED: cascade-01 @2025-08-13T18:30:00-04:00] [feature/azure-provisioning]**
      1.2.1 [x] Create resource group with proper naming and tags
      1.2.2 [x] Provision Azure SQL Database with firewall rules (minimal public access, no VNET)
      1.2.3 [x] Create Redis Cache instance with appropriate tier
      1.2.4 [x] Set up Blob Storage with containers and access policies
      1.2.5 [x] Create Key Vault with access policies and managed identity
  #1.3: Azure Functions setup [ ] (est: 0.5d) [CURRENT-TASK]
      1.3.1 [ ] Create Functions Consumption plan **[CHECKED OUT: Cascade-69 @2025-08-13T21:54:57-04:00] [feature/azure-functions-consumption-plan]**
      1.3.2 [ ] Create Function App with Python runtime
      1.3.3 [ ] Configure app settings from Key Vault using managed identity
      1.3.4 [ ] Set up connection strings and environment variables
      1.3.5 [ ] Configure CORS and authentication settings
  #1.4: Repository and development environment [ ] (est: 0.25d)
      1.4.1 [ ] Set up base repository structure (backend/frontend/docs/tests)
      1.4.2 [ ] Configure Python virtual environment and requirements.txt
      1.4.3 [ ] Create frontend scaffold with React/TypeScript/Tailwind
      1.4.4 [ ] Set up development configuration files (.env, .gitignore, etc.)
  #1.5: Static Web App configuration [ ] (est: 0.25d)
      1.5.1 [ ] Create Azure Static Web App resource
      1.5.2 [ ] Configure SWA to point API routes to Functions
      1.5.3 [ ] Set up custom domains and SSL certificates (if needed)
      1.5.4 [ ] Configure authentication providers (Azure AD)
  #1.T: Tests — unit, integration, acceptance for infra setup [ ] (est: 0.25d)

## 2: CI/CD and release-pack pipeline [ ] (est: 1 day)

  #2.1: SWA GitHub Actions deploy (tune `.github/workflows/azure-static-web-apps-*.yml`) [ ] (est: 0.25d)
      2.1.1 [ ] Configure SWA workflow with proper build commands and output directory
      2.1.2 [ ] Set up environment-specific deployment slots (staging/production)
      2.1.3 [ ] Configure secrets and environment variables in GitHub
      2.1.4 [ ] Test deployment pipeline with sample frontend changes
  #2.2: Functions build/deploy workflow (Python) [ ] (est: 0.25d)
      2.2.1 [ ] Create GitHub Actions workflow for Azure Functions deployment
      2.2.2 [ ] Configure Python build steps with requirements installation
      2.2.3 [ ] Set up deployment slots and blue-green deployment strategy
      2.2.4 [ ] Configure function app settings and connection strings
  #2.3: On tag push: build release-pack (zip) + attach to GitHub Release [ ] (est: 0.25d)
      2.3.1 [ ] Create release workflow triggered on tag creation
      2.3.2 [ ] Build and package all components (frontend, backend, docs)
      2.3.3 [ ] Generate release notes from commit history
      2.3.4 [ ] Attach release artifacts to GitHub Release
  #2.4: Draft manifest.json spec (version, commit, API versions) [ ] (est: 0.25d)
      2.4.1 [ ] Define manifest schema with version, commit hash, and API versions
      2.4.2 [ ] Create build script to generate manifest during CI
      2.4.3 [ ] Include dependency versions and build metadata
      2.4.4 [ ] Validate manifest format and required fields
  #2.T: Tests — unit, integration, acceptance for CI/CD + release-pack [ ] (est: 0.25d)

## 3: Chat interface (React/TS/Tailwind) [ ] (est: 2 days)

  #3.1: UI shell, routing, layout [x] (est: 0.25d) ✅ **[COMPLETED: cascade-02 @2025-01-15T11:00:00-05:00]**
  #3.2: Chat input, message list, timestamps [ ] (est: 0.5d) **[CHECKED OUT: cascade-02 @2025-01-15T11:15:00-05:00] [feature/chat-input-messages]**
  #3.3: Streaming display + retry/cancel [ ] (est: 0.5d)
  #3.4: Error/loading states, toasts [ ] (est: 0.25d)
  #3.5: Socket/client wiring for live updates [ ] (est: 0.25d)
  #3.6: Minimal admin panel shell (feature toggles) [ ] (est: 0.25d)
  #3.7: **REQUIRED** Cannasol logo integration [ ] (est: 0.15d)
      3.7.1 [ ] Add Cannasol logo to header/navigation bar
      3.7.2 [ ] Integrate logo in chat interface branding
      3.7.3 [ ] Add logo to loading states and splash screens
      3.7.4 [ ] Ensure responsive logo display across devices
  #3.T: Tests — unit (components), integration (API/socket), acceptance (chat flow) [ ] (est: 0.25d)

## 4: GROK integration + model router stub [ ] (est: 1 day)

  #4.1: Provider clients (GROK, placeholders for others) [x] (est: 0.25d) **[COMPLETED: augment-01 @2025-08-13T19:45:00-04:00]**
      4.1.1 [ ] Create base LLMProvider abstract class with standard interface
      4.1.2 [ ] Implement GROKProvider with API client and authentication
      4.1.3 [ ] Create placeholder providers for OpenAI, Claude, and local models
      4.1.4 [ ] Add provider configuration and credential management
  #4.2: ModelRouter.py (route by policy/env flag) [ ] (est: 0.25d)
      4.2.1 [ ] Design routing policy schema (cost, latency, capability-based)
      4.2.2 [ ] Implement router logic with fallback mechanisms
      4.2.3 [ ] Add environment-based provider selection
      4.2.4 [ ] Create configuration interface for routing rules
  #4.3: ContextManager.py (basic memory window) [ ] (est: 0.25d)
      4.3.1 [ ] Design conversation context schema and storage
      4.3.2 [ ] Implement sliding window memory management
      4.3.3 [ ] Add context compression and summarization logic
      4.3.4 [ ] Create context retrieval and injection mechanisms
  #4.4: Rate limiting/backoff + error normalization [ ] (est: 0.25d)
      4.4.1 [ ] Implement rate limiting with token bucket algorithm
      4.4.2 [ ] Add exponential backoff with jitter for retries
      4.4.3 [ ] Create error normalization layer for different providers
      4.4.4 [ ] Add circuit breaker pattern for provider failures
  #4.T: Tests — unit, integration, acceptance for model router [ ] (est: 0.25d)

## 5: Task generation + approval skeleton [ ] (est: 2 days)

  #5.1: Intent detection (rule-based MVP) [ ] (est: 0.5d)
      5.1.1 [ ] Define task-generating intent categories (email, document, query, etc.)
      5.1.2 [ ] Create rule-based classifier with keyword matching and patterns
      5.1.3 [ ] Implement confidence scoring and fallback handling
      5.1.4 [ ] Add intent validation and user confirmation prompts
  #5.2: Task schema, DB table, CRUD endpoints [ ] (est: 0.5d)
      5.2.1 [ ] Design task database schema with status, metadata, and audit fields
      5.2.2 [ ] Create database migration scripts and indexes
      5.2.3 [ ] Implement CRUD API endpoints with validation and serialization
      5.2.4 [ ] Add task querying, filtering, and pagination support
  #5.3: ApprovalHandler.py (approve/reject) [ ] (est: 0.5d)
      5.3.1 [ ] Create approval workflow state machine
      5.3.2 [ ] Implement approval/rejection logic with user context
      5.3.3 [ ] Add approval notifications and status tracking
      5.3.4 [ ] Create approval history and audit logging
  #5.4: UI approve/reject buttons + status updates [ ] (est: 0.5d)
      5.4.1 [ ] Design task approval interface with clear action buttons
      5.4.2 [ ] Implement real-time status updates and notifications
      5.4.3 [ ] Add task details view with approval history
      5.4.4 [ ] Create bulk approval functionality for multiple tasks
  #5.T: Tests — unit, integration, acceptance for tasking [ ] (est: 0.5d)

## 6: Inventory integration [ ] (est: 2 days)

  #6.1: InventoryClient.py with typed DTOs [ ] (est: 0.5d)
      6.1.1 [ ] Define inventory data models and DTOs with type annotations
      6.1.2 [ ] Create inventory client with connection management and retry logic
      6.1.3 [ ] Implement data serialization and deserialization
      6.1.4 [ ] Add client configuration and credential management
  #6.2: Read endpoints (list/filter) + pagination [ ] (est: 0.5d)
      6.2.1 [ ] Implement inventory listing with sorting and filtering
      6.2.2 [ ] Add pagination support with cursor-based or offset pagination
      6.2.3 [ ] Create search functionality with full-text and field-specific search
      6.2.4 [ ] Add caching layer for frequently accessed inventory data
  #6.3: Write endpoints (create/update) + validation [ ] (est: 0.5d)
      6.3.1 [ ] Implement inventory item creation with validation rules
      6.3.2 [ ] Add inventory update functionality with conflict resolution
      6.3.3 [ ] Create batch operations for bulk inventory changes
      6.3.4 [ ] Add inventory change tracking and audit logging
  #6.4: UI inventory viewer (basic) [ ] (est: 0.5d)
      6.4.1 [ ] Create inventory list view with search and filter controls
      6.4.2 [ ] Implement inventory item detail view and editing forms
      6.4.3 [ ] Add inventory data visualization (charts, summaries)
      6.4.4 [ ] Create inventory export functionality (CSV, Excel)
  #6.T: Tests — unit, integration, acceptance for inventory [ ] (est: 0.5d)

## 7: NL→SQL (inventory-only, whitelisted) [ ] (est: 1 day)

  #7.1: QueryTemplates.py (whitelist + param schema) [ ] (est: 0.25d)
      7.1.1 [ ] Define inventory query templates (list, search, filter, aggregate)
      7.1.2 [ ] Create parameter schema with validation rules
      7.1.3 [ ] Implement template registry with metadata
      7.1.4 [ ] Add template versioning and deprecation support
  #7.2: IntentDetector.py (map to template) [ ] (est: 0.25d)
      7.2.1 [ ] Create rule-based intent classification for inventory queries
      7.2.2 [ ] Implement parameter extraction from natural language
      7.2.3 [ ] Add confidence scoring for intent matches
      7.2.4 [ ] Create fallback handling for unrecognized intents
  #7.3: Executor.py (parameterized exec + limits) [ ] (est: 0.25d)
      7.3.1 [ ] Implement safe SQL execution with parameter binding
      7.3.2 [ ] Add query result formatting and serialization
      7.3.3 [ ] Create execution context with user permissions
      7.3.4 [ ] Add query logging and audit trail

## 8: Email integration (Microsoft Exchange) [ ] (est: 1 day)

  #8.1: Email summarize/draft/send [ ] (est: 0.5d)
      8.1.1 [ ] Implement email summarization endpoint (Graph API)
      8.1.2 [ ] Draft response generation with approval workflow
      8.1.3 [ ] Send email with priority, CC/BCC, and audit logging
  #8.2: Attachments and calendar [ ] (est: 0.25d)
      8.2.1 [ ] Attachment handling (upload/download, size limits)
      8.2.2 [ ] Calendar integration for meeting requests (create/invite)
      8.2.3 [ ] Error handling and permission checks
  #8.3: UI hooks [ ] (est: 0.15d)
      8.3.1 [ ] Chat actions: “Summarize”, “Draft”, “Send”
      8.3.2 [ ] Approval modal and status toasts
  #8.T: Tests — unit/integration for email [ ] (est: 0.1d)
      8.T.1 [ ] Unit tests for Graph client wrappers
      8.T.2 [ ] Integration tests for summarize/draft/send flow

## 9: Document management (templates) [ ] (est: 1 day)

  #9.1: Template store + validation [ ] (est: 0.5d)
      9.1.1 [ ] Template repository in Blob (versioned)
      9.1.2 [ ] Field validation and constraints
      9.1.3 [ ] Multi-format export (PDF/DOCX/XLSX)
  #9.2: Generation endpoints [ ] (est: 0.25d)
      9.2.1 [ ] Generate from template with data mapping
      9.2.2 [ ] Download/preview endpoints
  #9.3: UI hooks [ ] (est: 0.15d)
      9.3.1 [ ] “Generate Document” action with form input
      9.3.2 [ ] Result preview and download
  #9.T: Tests — unit/integration for documents [ ] (est: 0.1d)
      9.T.1 [ ] Unit tests for template validation
      9.T.2 [ ] Integration tests for generation + download

  #7.4: Guardrails: row limits, timeouts, RBAC check [ ] (est: 0.25d)
      7.4.1 [ ] Implement row count limits and pagination
      7.4.2 [ ] Add query timeout and resource limits
      7.4.3 [ ] Create RBAC checks for data access permissions
      7.4.4 [ ] Add SQL injection prevention and validation
  #7.T: Tests — unit, integration, acceptance for NL→SQL [ ] (est: 0.25d)

## 8: Email integration (Microsoft 365) [ ] (est: 1 day)

  #8.1: Microsoft Graph client setup [ ] (est: 0.25d)
      8.1.1 [ ] Register application in Azure AD with required permissions
      8.1.2 [ ] Configure Microsoft Graph SDK and authentication
      8.1.3 [ ] Set up service principal or managed identity for Graph access
      8.1.4 [ ] Test basic Graph API connectivity and permissions
  #8.2: Send mail endpoint + template support [ ] (est: 0.5d)
      8.2.1 [ ] Create email template system with variable substitution
      8.2.2 [ ] Implement send mail function with attachment support
      8.2.3 [ ] Add email validation and sanitization
      8.2.4 [ ] Create email queue and retry mechanism for failures
  #8.3: Basic UI action to trigger email [ ] (est: 0.25d)
      8.3.1 [ ] Add email composition interface in admin panel
      8.3.2 [ ] Create email preview functionality
      8.3.3 [ ] Implement send confirmation and status tracking
      8.3.4 [ ] Add email history and delivery status view
  #8.T: Tests — unit, integration, acceptance for email [ ] (est: 0.25d)

## 9: Document generation (PDF/DOCX) [ ] (est: 1 day)

  #9.1: Template storage (Blob) + metadata in SQL [ ] (est: 0.25d)
      9.1.1 [ ] Design document template schema and metadata structure
      9.1.2 [ ] Create blob storage containers for templates and generated docs
      9.1.3 [ ] Implement template upload and validation functionality
      9.1.4 [ ] Add template versioning and approval workflow
  #9.2: DOCX template merge and PDF export [ ] (est: 0.5d)
      9.2.1 [ ] Integrate python-docx for DOCX template processing
      9.2.2 [ ] Implement variable substitution and conditional content
      9.2.3 [ ] Add PDF conversion using LibreOffice or similar
      9.2.4 [ ] Create document generation queue and processing pipeline
  #9.3: Download link + versioning [ ] (est: 0.25d)
      9.3.1 [ ] Generate secure download links with expiration
      9.3.2 [ ] Implement document versioning and history tracking
      9.3.3 [ ] Add document access logging and permissions
      9.3.4 [ ] Create document management UI for admins
  #9.T: Tests — unit, integration, acceptance for document generation [ ] (est: 0.25d)

## 10: Auth (Azure AD SSO) + RBAC [ ] (est: 1 day)

  #10.1: Frontend MSAL setup + login flow [ ] (est: 0.25d)
      10.1.1 [ ] Configure MSAL library with Azure AD app registration
      10.1.2 [ ] Implement login/logout components and routing guards
      10.1.3 [ ] Add token refresh and silent authentication
      10.1.4 [ ] Create user profile display and session management
  #10.2: Backend token validation middleware [ ] (est: 0.25d)
      10.2.1 [ ] Implement JWT token validation middleware
      10.2.2 [ ] Add Azure AD token verification and claims extraction
      10.2.3 [ ] Create user context and session management
      10.2.4 [ ] Add API endpoint protection and authorization
  #10.3: Users/Permissions tables seeding + role checks [ ] (est: 0.25d)
      10.3.1 [ ] Design user, role, and permission database schema
      10.3.2 [ ] Create database migration scripts and seed data
      10.3.3 [ ] Implement role-based access control logic
      10.3.4 [ ] Add permission checking decorators and middleware
  #10.4: Permission matrix in UI (read-only MVP) [ ] (est: 0.25d)
      10.4.1 [ ] Create admin interface for viewing user permissions
      10.4.2 [ ] Implement role assignment and management UI
      10.4.3 [ ] Add permission audit trail and logging
      10.4.4 [ ] Create user access reports and analytics
  #10.T: Tests — unit, integration, acceptance for auth [ ] (est: 0.25d)

## 11: Telemetry/analytics (privacy-safe) [ ] (est: 1 day)

  #11.1: DDL for Analytics_* tables [ ] (est: 0.25d)
      11.1.1 [ ] Design analytics database schema (events, metrics, sessions)
      11.1.2 [ ] Create partitioned tables for time-series data
      11.1.3 [ ] Add indexes and constraints for query performance
      11.1.4 [ ] Implement data retention and archival policies
  #11.2: Telemetry instrumentation (latency, tokens, errors) [ ] (est: 0.25d)
      11.2.1 [ ] Add performance monitoring and latency tracking
      11.2.2 [ ] Implement token usage and cost tracking
      11.2.3 [ ] Create error tracking and categorization
      11.2.4 [ ] Add custom metrics and business KPIs
  #11.3: Redaction pipeline + config flag; sampling off by default [ ] (est: 0.25d)
      11.3.1 [ ] Implement PII detection and redaction pipeline
      11.3.2 [ ] Add configurable sampling rates and privacy controls
      11.3.3 [ ] Create data anonymization and aggregation rules
      11.3.4 [ ] Add consent management and opt-out mechanisms
  #11.4: Admin metrics view (p95, error rate) [ ] (est: 0.25d)
      11.4.1 [ ] Create real-time dashboard with key metrics
      11.4.2 [ ] Implement alerting for error rates and performance
      11.4.3 [ ] Add historical trend analysis and reporting
      11.4.4 [ ] Create exportable reports and data visualization
  #11.T: Tests — unit, integration, acceptance for telemetry/analytics [ ] (est: 0.25d)

## 12: Release-pack deliverable [ ] (est: 0.5 day)

  #12.1: Define manifest.json + api-schema.json (OpenAPI export) [ ] (est: 0.25d)
      12.1.1 [ ] Create comprehensive manifest schema with all metadata
      12.1.2 [ ] Generate OpenAPI specification from API endpoints
      12.1.3 [ ] Add API versioning and compatibility information
      12.1.4 [ ] Include dependency versions and system requirements
  #12.2: Pack db migrations + analytics-schema.json + deployment.json [ ] (est: 0.25d)
      12.2.1 [ ] Package all database migration scripts and schemas
      12.2.2 [ ] Create deployment configuration templates
      12.2.3 [ ] Add environment-specific configuration examples
      12.2.4 [ ] Generate installation and upgrade documentation
  #12.T: Tests — unit, integration, acceptance for release-pack [ ] (est: 0.25d)

## 13: Testing + deployment [ ] (est: 2 days)

  #13.1: Unit tests: router, tasking, NL→SQL templates [ ] (est: 0.75d)
  #13.2: Integration tests: Functions endpoints + SQL [ ] (est: 0.5d)
  #13.3: E2E happy path (chat → task → inventory → doc/email) [ ] (est: 0.5d)
  #13.4: Performance tests (k6/Locust) with PRD thresholds [ ] (est: 0.25d)
      13.4.1 [ ] Simple queries p95 < 2s; single integration p95 < 5s; multi-system p95 < 10s
      13.4.2 [ ] 20 concurrent users; 1000 req/hour sustained; graceful degradation verified
  #13.5: Acceptance tests (pytest-bdd/behave) mapped to PRD scenarios [ ] (est: 0.5d)

---

Note: Remember to update this plan after each completed task or subtask by:

  1. Checking off [ ] to [x].
  2. Removing [CURRENT-TASK] from the completed item.
  3. Adding [CURRENT-TASK] to the next active task or subtask.
