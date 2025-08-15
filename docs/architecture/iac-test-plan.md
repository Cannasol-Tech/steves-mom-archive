# Infrastructure as Code (IaC) Test Plan

## Overview

This document defines the Test-Driven Development (TDD) scope for Infrastructure as Code implementation, covering naming rules validation and SKU validation for Azure resources.

## Test Categories

### 1. Unit Tests

#### 1.1 Naming Convention Tests

**Scope**: Validate resource naming follows established conventions

**Test Cases**:

- `test_resource_group_naming_convention()`
  - Format: `rg-{project}-{environment}-{region}`
  - Example: `rg-stevesmom-prod-eastus`
  - Validates: lowercase, hyphens, max 90 chars

- `test_function_app_naming_convention()`
  - Format: `func-{project}-{environment}-{region}`
  - Example: `func-stevesmom-prod-eastus`
  - Validates: lowercase, hyphens, globally unique, max 60 chars

- `test_storage_account_naming_convention()`
  - Format: `st{project}{environment}{region}{random}`
  - Example: `ststevesmomprodeastus001`
  - Validates: lowercase, no hyphens, globally unique, 3-24 chars

- `test_sql_server_naming_convention()`
  - Format: `sql-{project}-{environment}-{region}`
  - Example: `sql-stevesmom-prod-eastus`
  - Validates: lowercase, hyphens, globally unique, max 63 chars

- `test_redis_cache_naming_convention()`
  - Format: `redis-{project}-{environment}-{region}`
  - Example: `redis-stevesmom-prod-eastus`
  - Validates: lowercase, hyphens, globally unique, max 63 chars

- `test_key_vault_naming_convention()`
  - Format: `kv-{project}-{environment}-{region}`
  - Example: `kv-stevesmom-prod-eastus`
  - Validates: lowercase, hyphens, globally unique, 3-24 chars

#### 1.2 SKU Validation Tests

**Scope**: Validate selected SKUs meet requirements and constraints

**Test Cases**:

- `test_function_app_consumption_sku()`
  - Validates: SKU is "Y1" (Consumption) or "FC1" (Flex Consumption)
  - Ensures: Cost optimization for MVP

- `test_sql_database_sku_selection()`
  - Validates: SKU is appropriate tier (Basic/Standard for MVP)
  - Ensures: Cost vs performance balance

- `test_redis_cache_sku_selection()`
  - Validates: SKU is Basic or Standard tier
  - Ensures: Appropriate for MVP workload

- `test_storage_account_replication_sku()`
  - Validates: Replication type (LRS/GRS) matches requirements
  - Ensures: Cost vs durability balance

#### 1.3 Tag Validation Tests

**Scope**: Validate required tags are present and correctly formatted

**Test Cases**:

- `test_required_tags_present()`
  - Validates: Environment, Project, Owner, CostCenter tags
  - Ensures: Governance compliance

- `test_tag_value_format()`
  - Validates: Tag values follow format rules
  - Ensures: Consistency across resources

#### 1.4 Location Validation Tests

**Scope**: Validate resources are deployed to correct regions

**Test Cases**:

- `test_primary_region_consistency()`
  - Validates: All resources in same primary region
  - Ensures: Latency optimization

- `test_allowed_regions()`
  - Validates: Only approved regions used
  - Ensures: Compliance with data residency

### 2. Integration Tests

#### 2.1 Resource Dependency Tests

**Scope**: Validate resource dependencies and relationships

**Test Cases**:

- `test_function_app_storage_dependency()`
  - Validates: Function App references correct Storage Account
  - Ensures: Runtime dependencies satisfied

- `test_function_app_key_vault_access()`
  - Validates: Function App has managed identity access to Key Vault
  - Ensures: Secure configuration retrieval

- `test_sql_firewall_configuration()`
  - Validates: SQL Server firewall allows Function App access
  - Ensures: Database connectivity

#### 2.2 Plan/What-If Tests

**Scope**: Validate expected resources will be created/modified

**Test Cases**:

- `test_bicep_plan_output()`
  - Validates: Plan shows expected resource creation
  - Ensures: No unexpected changes

- `test_resource_count_validation()`
  - Validates: Correct number of resources planned
  - Ensures: Complete deployment

- `test_no_destructive_changes()`
  - Validates: No existing resources will be deleted
  - Ensures: Safe deployment

### 3. Acceptance Tests

#### 3.1 End-to-End Deployment Tests

**Scope**: Validate complete infrastructure deployment

**Test Cases**:

- `test_complete_infrastructure_deployment()`
  - Validates: All resources deploy successfully
  - Ensures: Infrastructure is functional

- `test_application_connectivity()`
  - Validates: Function App can connect to all dependencies
  - Ensures: Application will function

- `test_security_configuration()`
  - Validates: Security settings are correctly applied
  - Ensures: Production-ready security

## Test Implementation Framework

### Tools and Libraries

- **Python**: pytest for test framework
- **Azure CLI**: Resource validation and querying
- **Bicep CLI**: Template validation and what-if operations
- **Azure SDK**: Programmatic resource validation

### Test Data Management

- **Test Fixtures**: Predefined resource configurations
- **Mock Data**: Simulated Azure responses for unit tests
- **Test Environments**: Isolated resource groups for testing

### Continuous Integration

- **Pre-commit Hooks**: Run naming validation tests
- **PR Validation**: Run full test suite on pull requests
- **Deployment Gates**: Require passing tests before deployment

## Test Execution Strategy

### Development Phase

1. Write failing tests first (TDD approach)
2. Implement IaC templates to make tests pass
3. Refactor while maintaining test coverage

### Validation Phase

1. Run unit tests on every commit
2. Run integration tests on PR creation
3. Run acceptance tests before deployment

### Monitoring Phase

1. Periodic validation of deployed resources
2. Drift detection through test execution
3. Compliance reporting based on test results

## Success Criteria

- **Unit Tests**: 100% pass rate for naming and SKU validation
- **Integration Tests**: 100% pass rate for resource dependencies
- **Acceptance Tests**: 100% pass rate for end-to-end scenarios
- **Coverage**: All IaC templates covered by tests
- **Performance**: Test suite completes in under 5 minutes
