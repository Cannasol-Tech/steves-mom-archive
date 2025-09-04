---
description: Story to standardize the Acceptance Testing Framework, reporting, and PRD traceability
---

# Story — Standardize Acceptance Testing Framework and Reporting

## Context
We need a robust, standardized acceptance testing setup that ensures PRD traceability and produces an artifact consumable by the Functionality Reports Dashboard on every run (local and CI). This story formalizes how we run, structure, and publish acceptance results.

- Source of truth for report format: `docs/standards/release-format.md`
- Owner/Repo: `Cannasol-Tech` / `steves-mom-archive`
- Local runs must set `releaseTag` to `"local"`
- `commit` must be the current HEAD short SHA
- Tests must be executed via Makefile targets only (see Makefile)

## User Story
- As a Product and Engineering team
- I want a standardized acceptance testing framework with PRD-mapped Gherkin scenarios and a consistent executive report
- So that we can validate business requirements end-to-end and publish reliable status for releases

## Definition of Done
1. Execution via Makefile
   - `make test-acceptance` runs the Behave suite in `tests/acceptance/features/`.
   - The target preserves the test exit code and fails CI appropriately.

2. Gherkin with PRD Traceability
   - Acceptance tests are written in Gherkin (`Given/When/Then`).
   - Each scenario is tagged with one or more PRD IDs (e.g., `@PRD-001`).
   - Scenarios clearly map to PRD requirements and are reflected in the final report under `requirements[]`.

3. Report Artifact on Every Run
   - The acceptance test run must always emit `final/executive-report.json`, even on failure.
   - The artifact conforms to Section 4.1 in `docs/standards/release-format.md`.
   - Local runs set `releaseTag: "local"`.
   - `commit` is populated from `git rev-parse --short HEAD` after committing changes.
   - `owner` = `Cannasol-Tech`, `repo` = `steves-mom-archive`.

4. CI Integration
   - CI bundles invoke `make test-acceptance` so that the artifact is generated and ready for releases.
   - Optional enrichment artifacts (`final/coverage-summary.json`, `final/unit-test-summary.json`) may be produced in CI.

5. Documentation
   - Document PRD tagging conventions, how to run locally, and where to find the artifact: `docs/testing/acceptance.md`.

6. Quality Gates (per global standards)
   - All tests pass 100%.
   - Overall coverage ≥ 85%.

## Acceptance Criteria
- Executing `make test-acceptance` locally:
  - Given a fresh environment (after `make setup`)
  - When I run `make test-acceptance`
  - Then Behave scenarios execute and `final/executive-report.json` is written to disk, with `releaseTag: "local"` and the current HEAD short SHA in `commit`.

- Gherkin-PRD mapping:
  - Given scenarios tagged with `@PRD-XYZ`
  - When the acceptance suite completes
  - Then `executive-report.json` includes `requirements[]` entries mapping those PRD IDs to the scenario names.

- Report format compliance:
  - Given the release format standard in `docs/standards/release-format.md`
  - When the run finishes
  - Then `final/executive-report.json` matches Section 4.1 (version, owner, repo, releaseTag, commit, createdAt, summary, scenarios with step outcomes, requirements mapping).

- CI behavior:
  - Given the CI workflow
  - When acceptance tests fail
  - Then the step still writes `final/executive-report.json` and the job fails with the appropriate exit code.

## Implementation Notes
- Runner:
  - Behave with JSON formatter writes to `tests/acceptance/.behave-report.json`.
- Transformation:
  - `scripts/acceptance_to_executive_report.py` converts Behave JSON into the canonical `final/executive-report.json` shape.
  - Environment variables supported for overrides:
    - `REPORT_OWNER`, `REPORT_REPO`, `REPORT_RELEASE_TAG`, `REPORT_VERSION`.
  - Defaults (local): owner `Cannasol-Tech`, repo `steves-mom-archive`, releaseTag `local`.
- Makefile wiring:
  - `make test-acceptance` runs Behave, transforms the output, ensures the artifact exists, and returns the original exit code.

## Traceability
- PRD items must be referenced via tags in scenarios, e.g., `@PRD-001`.
- The transformer aggregates these tags into `requirements[]` in the final report.

## Out of Scope
- Creating the executive GitHub Release in CI (handled by dedicated release workflows).
- Enforcing PRD ID validation against an external catalog (can be added later if desired).

## Follow-ups (optional)
- Add schema validation step in CI against `executive-report.schema.json`.
- Extend the report with evidence URLs for CI logs/screenshots when available.
