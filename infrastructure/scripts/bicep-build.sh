#!/usr/bin/env bash
set -euo pipefail

# Lint and build all Bicep files
# Prereqs: Azure CLI with Bicep (az bicep) or standalone bicep CLI

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$ROOT_DIR"

if command -v az >/dev/null 2>&1; then
  if az bicep version >/dev/null 2>&1; then
    echo "Using az bicep..."
    find . -name "*.bicep" -not -path "./node_modules/*" -print0 | while IFS= read -r -d '' file; do
      echo "Validating $file"
      az bicep build --file "$file" >/dev/null
    done
    echo "OK: Bicep files validate and build"
    exit 0
  fi
fi

if command -v bicep >/dev/null 2>&1; then
  echo "Using bicep CLI..."
  find . -name "*.bicep" -not -path "./node_modules/*" -print0 | while IFS= read -r -d '' file; do
    echo "Validating $file"
    bicep build "$file" >/dev/null
  done
  echo "OK: Bicep files validate and build"
else
  echo "ERROR: No bicep tooling found. Install Azure CLI (az bicep) or bicep CLI." >&2
  exit 1
fi
