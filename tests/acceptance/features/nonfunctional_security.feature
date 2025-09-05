@nfr @security @acceptance
Feature: Non-Functional - Security
  Ensure data protection and access control requirements are met

  @NFR-2.1
  Scenario: NFR-2.1 Data protection controls
    Given data at rest and in transit
    When encryption standards are applied
    Then AES-256 at rest and TLS 1.3 are enforced and keys managed via Key Vault

  @NFR-2.2
  Scenario: NFR-2.2 Access control protections
    Given authentication attempts and access patterns
    When controls are evaluated
    Then lockouts, IP whitelisting, VPN needs, and session termination are enforced
