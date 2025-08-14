#!/usr/bin/env bash
set -euo pipefail

# What-if a resource group deployment for main.bicep
# Usage: ./scripts/bicep-whatif.sh <resource-group> [location] [parameters-file]
# Requires: az CLI with bicep (az bicep) and an existing resource group

if ! command -v az >/dev/null 2>&1; then
  echo "ERROR: Azure CLI (az) not found" >&2
  exit 1
fi

RG_NAME=${1:-}
LOCATION=${2:-eastus}
PARAM_FILE=${3:-infrastructure/parameters/dev.parameters.json}

if [[ -z "${RG_NAME}" ]]; then
  echo "Usage: $0 <resource-group> [location] [parameters-file]" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$ROOT_DIR"

if ! az group show -n "$RG_NAME" >/dev/null 2>&1; then
  echo "Resource group '$RG_NAME' does not exist. Create it first:\n  az group create -n $RG_NAME -l $LOCATION" >&2
  exit 3
fi

# Optional secure password param via env var
EXTRA_PARAMS=()
if [[ -n "${SQL_ADMIN_PASSWORD:-}" ]]; then
  EXTRA_PARAMS+=(--parameters sqlAdminPassword="$SQL_ADMIN_PASSWORD")
fi

set -x
az deployment group what-if \
  --resource-group "$RG_NAME" \
  --template-file main.bicep \
  --parameters @"$PARAM_FILE" \
  "${EXTRA_PARAMS[@]}"
set +x
