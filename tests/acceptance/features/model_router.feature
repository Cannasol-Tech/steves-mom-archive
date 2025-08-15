Feature: Model Router End-to-End Scenarios
  As a user of the AI system
  I want the model router to behave correctly under various conditions
  So that the system is reliable, cost-effective, and performant.

  Background:
    Given a ModelRouter instance

  Scenario: Cost-conscious business user gets cheapest responses
    Given a "cost_optimized" routing policy with a max cost of $0.05
    And a "local" provider is configured with a cost of $0.01 and priority 5
    And a "grok" provider is configured with a cost of $0.08 and priority 10
    When a business user sends a query
    Then the router should select the "local" provider
    And the "grok" provider should not be called

  Scenario: Production system fails over to backup provider
    Given a "failover" routing policy with fallback enabled
    And a primary "grok" provider is configured to fail
    And a backup "local" provider is configured to succeed
    When a user sends a technical query
    Then the router should select the "local" provider after the primary fails

  Scenario: Complex queries are routed by AI capability
    Given a "capability_based" routing policy requiring "REASONING" and "CODE_GENERATION"
    And a "local" provider is configured with "TEXT_GENERATION" capability and priority 10
    And a "grok" provider is configured with "REASONING" and "CODE_GENERATION" capabilities and priority 5
    When a user sends a query requiring code generation
    Then the router should select the "grok" provider

  Scenario: Administrator modifies routing policies at runtime
    Given a "local" provider is configured with priority 5 and 60 max requests per minute
    When the administrator loads a new configuration with priority 10 and 120 max requests per minute
    Then the router's configuration should be updated successfully
    And the system should continue to operate correctly

  Scenario: DevOps engineer configures router from environment variables
    Given the environment is configured for "failover" routing with a "local" provider
    When the router is created from the environment
    Then its configuration should match the environment variables

  Scenario: Operations team monitors system health and performance
    Given a "local" provider is configured for health checks
    When 3 requests are sent to the router
    Then the provider status should report as "healthy"
    And show 3 recent requests
