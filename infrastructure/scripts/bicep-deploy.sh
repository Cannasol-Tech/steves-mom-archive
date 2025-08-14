#!/usr/bin/env bash
set -euo pipefail

# Deploy main.bicep to a resource group
# Usage: ./scripts/bicep-deploy.sh <resource-group> [location] [parameters-file]
# Requires: az CLI and login (az login)

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
  echo "Creating resource group '$RG_NAME' in $LOCATION"
  az group create -n "$RG_NAME" -l "$LOCATION" >/dev/null
fi

EXTRA_PARAMS=()
if [[ -n "${SQL_ADMIN_PASSWORD:-}" ]]; then
  EXTRA_PARAMS+=(--parameters sqlAdminPassword="$SQL_ADMIN_PASSWORD")
fi

set -x
az deployment group create \
  --resource-group "$RG_NAME" \
  --template-file main.bicep \
  --parameters @"$PARAM_FILE" \
  "${EXTRA_PARAMS[@]}"
set +x
