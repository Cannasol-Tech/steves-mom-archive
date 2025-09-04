@skip @security @acceptance
Feature: Security and Access Control
  Ensure authenticated and authorized access with auditing

  @FR-4.1
  Scenario: FR-4.1 Azure AD Authentication
    Given the user signs in with @cannasolusa.com
    When authentication completes
    Then a valid session is established with SSO and timeout policies

  @FR-4.2
  Scenario: FR-4.2 Role-based authorization
    Given users have assigned roles and permissions
    When accessing protected resources
    Then access is granted/denied according to RBAC and classification

  @FR-4.3
  Scenario: FR-4.3 Audit and compliance logging
    Given system events occur
    When actions are performed on sensitive resources
    Then audit logs capture activity and provide export capabilities
