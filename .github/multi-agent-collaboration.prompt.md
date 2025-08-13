# Multi-Agent Collaboration Prompt

You are an AI coding agent working in a collaborative multi-agent system. Your coordination is managed through `docs/planning/multi-agent-sync.md` while following the implementation roadmap in `docs/planning/implementation-plan.md`.

**Multi-Agent Coordination Protocol:**

## 1. Initial Setup

- Check `docs/planning/multi-agent-sync.md` for your assigned agent ID
- If first time, register yourself in the "Active Agents" section
- Review current sprint goals and priorities

## 2. Task Selection & Checkout

Before starting any work:

- Scan the "Available Tasks" section for unclaimed items
- Check task dependencies and prerequisites
- Update the implementation plan by adding your agent ID and branch name:

  ```markdown
  - [ ] Task description **[CHECKED OUT: Agent-ID @timestamp] [feature/user-authentication]**
  ```

- Move the task to "In Progress" section in multi-agent-sync.md:

  ```markdown
  ## In Progress
  | Task ID | Description | Agent | Branch | Started | Dependencies | Notes |
  |---------|-------------|-------|--------|---------|--------------|-------|
  | 3.1 | Weekly Slot Management | cascade-02 | feature/weekly-scheduling | 2025-01-15T10:30Z | 2.4 complete | Working on capacity logic |
  ```

## 3. Dependency & Interface Documentation

When creating shared components:

```markdown
## Shared Interfaces & Contracts
### [Component/Module Name]
- **Owner:** [Your-Agent-ID]
- **Location:** `path/to/module`
- **Public API:**
  ```typescript
  interface ModuleName {
    methodName(param: Type): ReturnType;
  }
  ```

- **Dependencies:** [List required modules]
- **Consumers:** [Agents/modules using this]
- **Status:** Draft | Stable | Deprecated

```

## 4. Task Failure Handling

If you encounter a blocking issue:

- Move task to "Failed Tasks" section:

  ```markdown
  ## Failed Tasks
  | Task ID | Agent | Failed At | Error Type | Error Message | Can Retry |
  |---------|-------|-----------|------------|---------------|-----------|
  | 2.3 | cascade-01 | 2025-01-15T14:20Z | TestFailure | Auth middleware test timeout | Yes |
  ```

- Pick a different unclaimed task immediately
- If second agent fails same task, escalate to human:

  ```markdown
  ## 🚨 HUMAN INTERVENTION REQUIRED
  | Task ID | Failed Agents | Common Error | Recommendation |
  |---------|---------------|--------------|----------------|
  | 2.3 | cascade-01, cascade-04 | TestFailure: Auth timeout | Possible environment issue |
  ```

## 5. Progress Synchronization

After completing each task:

- Update implementation plan checkbox: `- [x] Task description ✅ **[COMPLETED: Agent-ID @timestamp]**`
- Run test suite and document results:

  ```markdown
  ## Test Results
  | Task ID | Agent | Unit Tests | Integration Tests | Acceptance Tests | Coverage |
  |---------|-------|------------|-------------------|------------------|----------|
  | 2.1 | cascade-01 | 48/48 ✅ | 12/12 ✅ | 8/8 ✅ | 95% |
  ```

- Move to "Completed Tasks" with final status:

  ```markdown
  ## Completed Tasks
  | Task ID | Agent | Branch | Duration | Files Modified | Merged |
  |---------|-------|--------|----------|----------------|--------|
  | 2.1 | cascade-01 | feature/request-creation | 4h | 12 files | ✅ |
  ```

## 6. Testing Coordination

- Any agent can run the test suite at any time
- Before marking task complete, run: `make test && make acceptance`
- Document test results in sync file
- If tests fail after your changes:

  ```markdown
  ## Test Failures
  | Agent | Task | Test Suite | Failing Tests | Status |
  |-------|------|------------|---------------|--------|
  | cascade-02 | 3.1 | Integration | test_capacity_limits | Investigating |
  ```

## 7. Branch Management

- Create feature branch as specified in implementation plan
- Format: `feature/descriptive-feature-name`
- Push regularly to prevent work loss
- Document branch in both sync file and implementation plan

## 8. Communication Log

For important updates:

```markdown
## Communication Log
| Timestamp | From | To | Message | Action Required |
|-----------|------|----|---------|-----------------|
| 2025-01-15T11:45Z | cascade-02 | ALL | Updated user service API | Review new endpoints |
| 2025-01-15T15:30Z | cascade-03 | cascade-01 | Need help with auth integration | Pair programming session |
```

## 9. Daily Synchronization Points

- **Morning Check:** Review failed tasks, check for human escalations
- **Task Completion:** Update progress, run tests, document results
- **Before New Task:** Check dependencies and interface updates

## 10. Code Quality Checklist

Before marking complete:

- [ ] All tests passing
- [ ] Code follows project style guide
- [ ] Documentation updated
- [ ] No linting errors
- [ ] Coverage meets minimums
- [ ] Branch ready to merge

Always maintain atomic commits with descriptive messages referencing task IDs. The sync file is the single source of truth - check it before any major decision. If uncertain about task status, check the sync file first.
