---
description: How to write and run acceptance tests with PRD traceability and executive report generation
---

# Acceptance Testing Guide

This project standardizes acceptance testing using Gherkin (Behave) with PRD mapping and a required executive report artifact for each run.

- Standard reference: `docs/standards/release-format.md`
- Owner/Repo for reports: `Cannasol-Tech` / `steves-mom-archive`
- Local runs set `releaseTag` to `local`

## Writing Scenarios
- Location: `tests/acceptance/features/`
- Use `.feature` files in Gherkin syntax.
- Tag each scenario with one or more PRD IDs: `@PRD-###`
- Optional tags: `@smoke`, `@critical`, etc.

Example `tests/acceptance/features/sample_acceptance.feature`:
```gherkin
@PRD-001 @smoke
Feature: Sample acceptance scaffold
  As a team
  I want a minimal acceptance test scaffold
  So that the Make target can demonstrate report generation

  Scenario: Placeholder passes trivially
    Given a working repository
    When I run a no-op acceptance step
    Then the placeholder should pass
```

Corresponding step definitions in `tests/acceptance/features/steps/` (example `sample_steps.py`) provide the Python functions for `Given/When/Then` steps.

## Running Locally
- Use Make targets only (do not run Behave directly):
```
make setup        # one-time env setup
make test-acceptance
```
- Behavior:
  - Executes Behave and writes JSON to `tests/acceptance/.behave-report.json`.
  - Transforms to `final/executive-report.json` via `scripts/acceptance_to_executive_report.py`.
  - Preserves the test exit code.
  - Local runs set `releaseTag: "local"` and populate `commit` from `git rev-parse --short HEAD`.

## Report Format
The transformer outputs `final/executive-report.json` complying with Section 4.1 of `docs/standards/release-format.md`, including:
- `version`, `owner`, `repo`, `releaseTag`, `commit`, `createdAt`
- `summary` totals
- `scenarios[]` with step-level statuses
- `requirements[]` built from `@PRD-*` tags mapping to scenario names

Environment overrides are supported:
- `REPORT_OWNER`, `REPORT_REPO`, `REPORT_RELEASE_TAG`, `REPORT_VERSION`

## CI Expectations
- CI should call `make test-acceptance`.
- Even on failure, `final/executive-report.json` must be present for release workflows to consume.
- Optional: also emit `final/unit-test-summary.json` and `final/coverage-summary.json` in CI.

## Troubleshooting
- If `final/executive-report.json` is missing, re-run `make test-acceptance` and check for errors in `scripts/acceptance_to_executive_report.py`.
- Ensure you have committed changes before running so `commit` is a valid short SHA.
