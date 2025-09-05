@nfr @performance @acceptance
Feature: Non-Functional - Performance and Scalability
  Validate performance targets and scalability characteristics

  @NFR-1.1
  Scenario: NFR-1.1 Response time thresholds
    Given representative workloads
    When requests are processed
    Then simple queries complete < 2s, single-integration < 5s, multi-system < 10s

  @NFR-1.2
  Scenario: NFR-1.2 Throughput and concurrency
    Given 20 concurrent users
    When the system processes 1000 requests/hour
    Then it maintains service quality with queueing during peaks

  @NFR-1.3
  Scenario: NFR-1.3 Scalability characteristics
    Given increased load and data volumes
    When scaling operations are applied
    Then the system scales horizontally/vertically and meets DB targets
