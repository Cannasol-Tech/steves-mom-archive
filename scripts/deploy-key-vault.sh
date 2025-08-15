#!/bin/bash

# Deploy Azure Key Vault for Steve's Mom AI Chatbot
# Usage: ./deploy-key-vault.sh [environment] [resource-group]

set -e

# Configuration
ENVIRONMENT="${1:-dev}"
RESOURCE_GROUP="${2:-rg-steves-mom}"
LOCATION="${3:-eastus}"
PROJECT_NAME="stevesmom"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Resource names following naming conventions
KEY_VAULT_NAME="kv-${PROJECT_NAME}-${ENVIRONMENT}-${LOCATION}"

log_info "Deploying Key Vault..."
log_info "Name: $KEY_VAULT_NAME"
log_info "Resource Group: $RESOURCE_GROUP"
log_info "SKU: Standard"

# Get current user object ID for access policy
CURRENT_USER_ID=$(az ad signed-in-user show --query "id" -o tsv)

# Check if Key Vault already exists
if az keyvault show --name "$KEY_VAULT_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    log_warning "Key Vault $KEY_VAULT_NAME already exists. Skipping creation."
else
    log_info "Creating Key Vault..."
    az keyvault create \
        --name "$KEY_VAULT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --sku "standard" \
        --enabled-for-template-deployment true \
        --enable-soft-delete true \
        --soft-delete-retention-days 30 \
        --enable-purge-protection false \
        --enable-rbac-authorization false \
        --tags \
            Environment="$ENVIRONMENT" \
            Project="$PROJECT_NAME" \
            Owner="cannasol-dev-team" \
            CostCenter="engineering" \
            CreatedBy="deployment-script"
    
    log_success "Key Vault created successfully"
fi

# Set access policy for current user
log_info "Setting access policy for current user..."
az keyvault set-policy \
    --name "$KEY_VAULT_NAME" \
    --object-id "$CURRENT_USER_ID" \
    --secret-permissions get list set delete backup restore recover purge \
    --key-permissions get list create delete backup restore recover purge \
    --certificate-permissions get list create delete backup restore recover purge \
    --output none

log_success "Access policy configured"

# Create initial placeholder secrets
log_info "Creating initial placeholder secrets..."

SECRETS=(
    "sql-connection-string:placeholder-will-be-updated-by-pipeline"
    "redis-connection-string:placeholder-will-be-updated-by-pipeline"
    "storage-connection-string:placeholder-will-be-updated-by-pipeline"
    "grok-api-key:placeholder-update-with-actual-api-key"
    "openai-api-key:placeholder-update-with-actual-api-key"
    "anthropic-api-key:placeholder-update-with-actual-api-key"
    "app-config:{\"environment\":\"${ENVIRONMENT}\",\"debug\":$([ "$ENVIRONMENT" != "prod" ] && echo "true" || echo "false"),\"logLevel\":\"$([ "$ENVIRONMENT" == "prod" ] && echo "INFO" || echo "DEBUG")\"}"
)

for secret_pair in "${SECRETS[@]}"; do
    SECRET_NAME=$(echo "$secret_pair" | cut -d':' -f1)
    SECRET_VALUE=$(echo "$secret_pair" | cut -d':' -f2-)
    
    if az keyvault secret show --vault-name "$KEY_VAULT_NAME" --name "$SECRET_NAME" &>/dev/null; then
        log_warning "Secret '$SECRET_NAME' already exists. Skipping."
    else
        az keyvault secret set \
            --vault-name "$KEY_VAULT_NAME" \
            --name "$SECRET_NAME" \
            --value "$SECRET_VALUE" \
            --output none
        log_success "Created secret: $SECRET_NAME"
    fi
done

# Get Key Vault URI
KEY_VAULT_URI=$(az keyvault show --name "$KEY_VAULT_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.vaultUri" -o tsv)

# Save deployment info
cat > ".azure-keyvault-info" << EOF
KEY_VAULT_NAME=$KEY_VAULT_NAME
KEY_VAULT_URI=$KEY_VAULT_URI
CURRENT_USER_ID=$CURRENT_USER_ID
SECRETS=${SECRETS[*]}
EOF

log_success "Key Vault deployment completed!"
log_info "Connection details saved to .azure-keyvault-info"

# Display Key Vault info
log_info "Key Vault Details:"
log_info "  Name: $KEY_VAULT_NAME"
log_info "  URI: $KEY_VAULT_URI"
log_info "  SKU: Standard"
log_info "  Soft Delete: Enabled (30 days)"
log_info "  Purge Protection: Disabled (dev/staging)"
log_info "  Secrets Created: ${#SECRETS[@]}"

log_warning "Remember to update placeholder secrets with actual values:"
log_warning "  - API keys for GROK, OpenAI, Anthropic"
log_warning "  - Connection strings will be updated by deployment pipeline"
