# Infrastructure (Bicep)

This folder contains Bicep templates for provisioning the MVP infrastructure using the cheapest practical SKUs.

- Orchestrator: `main.bicep`
- Modules: `modules/`
  - `storage.bicep` — StorageV2, Standard LRS, Hot
  - `functionapp.bicep` — Linux Function App on Consumption (Y1)
  - `sql.bicep` — Azure SQL (serverless, auto-pause)
  - `redis.bicep` — Azure Cache for Redis Basic C0
  - `keyvault.bicep` — Key Vault Standard
  - `swa.bicep` — Azure Static Web Apps Free
  - `appinsights.bicep` — Application Insights (connected to Function App/SWA)

Notes:
- Target scope: resource group
- All resources must include tags defined in `docs/architecture/naming.md`
- Keep modules minimal and composable; parameters are typed and documented.
