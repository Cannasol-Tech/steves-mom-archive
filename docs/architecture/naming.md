# Azure Resource Naming Conventions

## Overview

This document defines the standardized naming conventions for all Azure resources in the Steve's Mom AI Chatbot project. These conventions ensure consistency, clarity, and compliance with Azure naming requirements.

## General Principles

1. **Consistency**: All resources follow the same pattern within their category
2. **Clarity**: Names clearly indicate purpose and environment
3. **Compliance**: Names meet Azure length and character requirements
4. **Uniqueness**: Globally unique names include random suffixes where required

## Environment Abbreviations

| Environment | Abbreviation |
|-------------|--------------|
| Development | `dev` |
| Staging     | `staging` |
| Production  | `prod` |

## Region Abbreviations

| Azure Region | Abbreviation |
|--------------|--------------|
| East US      | `eastus` |
| East US 2    | `eastus2` |
| West US 2    | `westus2` |
| Central US   | `centralus` |

## Resource Naming Conventions

### 1. Resource Groups
**Pattern**: `rg-{project}-{environment}-{region}`

**Examples**:
- `rg-stevesmom-dev-eastus`
- `rg-stevesmom-staging-eastus`
- `rg-stevesmom-prod-eastus`

**Constraints**:
- Length: 1-90 characters
- Characters: Alphanumeric, hyphens, periods, parentheses, underscores
- Cannot end with period

### 2. Azure Functions
**Pattern**: `func-{project}-{environment}-{region}`

**Examples**:
- `func-stevesmom-dev-eastus`
- `func-stevesmom-staging-eastus`
- `func-stevesmom-prod-eastus`

**Constraints**:
- Length: 2-60 characters
- Characters: Alphanumeric and hyphens
- Must be globally unique
- Cannot start or end with hyphen

### 3. Storage Accounts
**Pattern**: `st{project}{environment}{region}{random}`

**Examples**:
- `ststevesmomdeveastus001`
- `ststevesmomstgeastus001`
- `ststevesmomprodeastus001`

**Constraints**:
- Length: 3-24 characters
- Characters: Lowercase letters and numbers only
- Must be globally unique
- No hyphens or special characters

### 4. Azure SQL Server
**Pattern**: `sql-{project}-{environment}-{region}`

**Examples**:
- `sql-stevesmom-dev-eastus`
- `sql-stevesmom-staging-eastus`
- `sql-stevesmom-prod-eastus`

**Constraints**:
- Length: 1-63 characters
- Characters: Lowercase letters, numbers, and hyphens
- Must be globally unique
- Cannot start or end with hyphen

### 5. Azure SQL Database
**Pattern**: `sqldb-{project}-{environment}`

**Examples**:
- `sqldb-stevesmom-dev`
- `sqldb-stevesmom-staging`
- `sqldb-stevesmom-prod`

**Constraints**:
- Length: 1-128 characters
- Characters: Unicode letters, numbers, hyphens
- Cannot contain spaces or special characters

### 6. Redis Cache
**Pattern**: `redis-{project}-{environment}-{region}`

**Examples**:
- `redis-stevesmom-dev-eastus`
- `redis-stevesmom-staging-eastus`
- `redis-stevesmom-prod-eastus`

**Constraints**:
- Length: 1-63 characters
- Characters: Alphanumeric and hyphens
- Must be globally unique
- Cannot start or end with hyphen

### 7. Key Vault
**Pattern**: `kv-{project}-{environment}-{region}`

**Examples**:
- `kv-stevesmom-dev-eastus`
- `kv-stevesmom-staging-eastus`
- `kv-stevesmom-prod-eastus`

**Constraints**:
- Length: 3-24 characters
- Characters: Alphanumeric and hyphens
- Must be globally unique
- Cannot start with number

### 8. Static Web App
**Pattern**: `swa-{project}-{environment}-{region}`

**Examples**:
- `swa-stevesmom-dev-eastus`
- `swa-stevesmom-staging-eastus`
- `swa-stevesmom-prod-eastus`

**Constraints**:
- Length: 2-60 characters
- Characters: Alphanumeric and hyphens
- Must be globally unique

### 9. Application Insights
**Pattern**: `ai-{project}-{environment}-{region}`

**Examples**:
- `ai-stevesmom-dev-eastus`
- `ai-stevesmom-staging-eastus`
- `ai-stevesmom-prod-eastus`

**Constraints**:
- Length: 1-260 characters
- Characters: Alphanumeric, hyphens, periods, parentheses

### 10. Log Analytics Workspace
**Pattern**: `law-{project}-{environment}-{region}`

**Examples**:
- `law-stevesmom-dev-eastus`
- `law-stevesmom-staging-eastus`
- `law-stevesmom-prod-eastus`

**Constraints**:
- Length: 4-63 characters
- Characters: Alphanumeric and hyphens
- Cannot start or end with hyphen

## Required Tags

All resources must include the following tags:

| Tag Name | Description | Example Values |
|----------|-------------|----------------|
| Environment | Deployment environment | `dev`, `staging`, `prod` |
| Project | Project identifier | `stevesmom` |
| Owner | Team or individual responsible | `cannasol-dev-team` |
| CostCenter | Cost allocation identifier | `engineering` |
| CreatedBy | Creation method | `iac`, `manual`, `terraform` |
| CreatedDate | Creation date | `2025-08-13` |

## Validation Rules

### Automated Validation
- All names must pass regex validation for their resource type
- Names must not exceed maximum length constraints
- Required tags must be present and non-empty
- Environment values must match approved list

### Manual Review Points
- Naming consistency across related resources
- Appropriate environment designation
- Cost center alignment with project budget
- Owner assignment accuracy

## Implementation Notes

### For Bicep Templates
```bicep
// Example parameter validation
@minLength(3)
@maxLength(24)
@description('Storage account name following naming convention')
param storageAccountName string = 'st${projectName}${environment}${location}${uniqueString(resourceGroup().id)}'
```

### For Terraform
```hcl
# Example local values for naming
locals {
  project_name = "stevesmom"
  environment  = var.environment
  location     = var.location
  
  resource_group_name = "rg-${local.project_name}-${local.environment}-${local.location}"
  function_app_name   = "func-${local.project_name}-${local.environment}-${local.location}"
}
```

## Exception Handling

### Legacy Resources
- Existing resources that don't follow conventions should be documented
- Migration plan should be created for critical resources
- New resources must follow current conventions

### Third-Party Requirements
- Some services may require specific naming patterns
- Document exceptions with business justification
- Maintain consistency where possible

## Maintenance

This document should be reviewed and updated:
- When new Azure services are adopted
- When naming conflicts arise
- Quarterly as part of governance review
- Before major infrastructure changes
