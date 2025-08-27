---
feature_id: 1.4.MY
name: Incremental mypy hardening for backend/ai/
owner: augment-02
branch: feature/mypy-hardening-ai
status: Draft
created: 2025-08-27T12:00:00-04:00
---

# Feature Prompt: Incremental mypy hardening for backend/ai/

## Goal

Gradually enable stricter mypy rules in backend/ai/ without breaking CI, improving type safety and maintainability.

## Scope

- Enable warn-unused-ignores, warn-redundant-casts globally (already present) and confirm enforcement.
- Per-module strictness: base_provider.py, config_manager.py, model_router.py, each provider module DTOs.
- Remove package-level ignore_errors for ai.* incrementally by module.

## Non-Goals

- Refactoring business logic beyond what is necessary for typing.
- Changing provider runtime behavior.

## Deliverables

- Updated mypy.ini with per-module overrides and reduced ignores.
- DTOs and explicit Protocols/TypedDicts for routing policies and provider interfaces.
- Tests: unit/integration green; mypy clean for scoped modules.
- Updated planning artifacts and sync entries.

## Public API and Interfaces

- backend/ai/providers/base.py
  - Abstract interface of LLMProvider
  - DTOs: Message, ModelConfig, ProviderError
- backend/ai/model_router.py
  - RoutingPolicy, RoutingStrategy, ModelRouter API
  - Protocols for provider capability and cost estimation

## TDD Plan

1) Write/adjust unit tests for type-level guarantees (where feasible) and runtime behavior that may be affected by typing changes.
2) Add mypy strict flags per module and run mypy expecting failures.
3) Implement minimal fixes (annotations, DTOs, Protocols) until mypy is clean.
4) Run `make test` to ensure no regressions.

## Risks and Mitigations

- Risk: Over-tightening breaks builds. Mitigation: module-by-module flags, incremental PRs.
- Risk: Complex provider signatures. Mitigation: introduce Pydantic DTOs or TypedDicts.

## Acceptance Criteria

- mypy strict flags enabled for 3+ backend/ai modules with 0 errors in those modules.
- make test passes locally; CI green.
- Implementation plan and sync updated with results and test table entries.
