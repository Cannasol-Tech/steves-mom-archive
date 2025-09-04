@skip @tasks @acceptance
Feature: Task Generation and Workflow
  In order to automate work
  As a user
  I want generated tasks to be approved and executed

  @FR-2.1
  Scenario: FR-2.1 Intelligent Task Generation
    Given a complex user request requiring multiple actions
    When the system analyzes the request
    Then tasks are generated with types, metadata, and confidence scores

  @FR-2.2
  Scenario: FR-2.2 Approval Workflow
    Given tasks are generated for a request
    When the user reviews the tasks
    Then they can approve, reject, or modify them with history captured

  @FR-2.3
  Scenario: FR-2.3 Task Execution and Progress
    Given an approved task with an available agent
    When execution starts
    Then progress is tracked and status updates are emitted
