# User Story 007: Infrastructure as Code (IaC)

**As a DevOps engineer**, I want to define all cloud resources using Bicep **so that** infrastructure is version-controlled and repeatable.

## Description
This story covers the creation of modular Bicep templates for all Azure resources required by the application, including storage, database, Key Vault, and hosting platforms.

## Acceptance Criteria
- Bicep modules are created for each major resource type (e.g., `storage.bicep`, `sql.bicep`).
- The `main.bicep` file orchestrates the deployment of all modules.
- Naming conventions and resource tagging are enforced as per `docs/architecture/naming.md`.
- Parameter files (`dev.parameters.json`, `staging.parameters.json`) are used to configure environment-specific settings.
- The deployment scripts (`bicep-deploy.sh`) work correctly.
