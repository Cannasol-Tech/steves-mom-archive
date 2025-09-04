@skip @nfr @reliability @acceptance
Feature: Non-Functional - Reliability
  Validate availability and error handling

  @NFR-3.1
  Scenario: NFR-3.1 Availability targets
    Given normal operations
    When monitoring the system during business hours
    Then uptime meets 99.5% with redundancy and failover

  @NFR-3.2
  Scenario: NFR-3.2 Error handling and resilience
    Given transient failures and faults
    When they occur
    Then errors are handled gracefully with retries, logging, alerts, and user-friendly fallbacks
