#!/bin/bash

# Deploy Azure Storage Account for Steve's Mom AI Chatbot
# Usage: ./deploy-storage-account.sh [environment] [resource-group]

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

# Generate unique storage account name (must be globally unique)
RANDOM_SUFFIX=$(openssl rand -hex 3)
STORAGE_NAME="st${PROJECT_NAME}${ENVIRONMENT}${LOCATION}${RANDOM_SUFFIX}"

# Ensure storage name is within limits (3-24 characters, lowercase alphanumeric)
if [ ${#STORAGE_NAME} -gt 24 ]; then
    STORAGE_NAME="st${PROJECT_NAME}${ENVIRONMENT}$(echo $LOCATION | cut -c1-3)${RANDOM_SUFFIX}"
fi

log_info "Deploying Storage Account..."
log_info "Name: $STORAGE_NAME"
log_info "Resource Group: $RESOURCE_GROUP"
log_info "SKU: Standard_LRS"

# Check if storage account already exists
if az storage account show --name "$STORAGE_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    log_warning "Storage Account $STORAGE_NAME already exists. Skipping creation."
else
    log_info "Creating Storage Account..."
    az storage account create \
        --name "$STORAGE_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --sku "Standard_LRS" \
        --kind "StorageV2" \
        --access-tier "Hot" \
        --https-only true \
        --min-tls-version "TLS1_2" \
        --allow-blob-public-access false \
        --tags \
            Environment="$ENVIRONMENT" \
            Project="$PROJECT_NAME" \
            Owner="cannasol-dev-team" \
            CostCenter="engineering" \
            CreatedBy="deployment-script"
    
    log_success "Storage Account created successfully"
fi

# Get storage account key
log_info "Retrieving storage account key..."
STORAGE_KEY=$(az storage account keys list --resource-group "$RESOURCE_GROUP" --account-name "$STORAGE_NAME" --query "[0].value" -o tsv)

# Create required blob containers
log_info "Creating blob containers..."
CONTAINERS=("templates" "generated" "temp" "classified-public" "classified-secret" "classified-topsecret")

for container in "${CONTAINERS[@]}"; do
    if az storage container show --name "$container" --account-name "$STORAGE_NAME" --account-key "$STORAGE_KEY" &>/dev/null; then
        log_warning "Container '$container' already exists. Skipping."
    else
        az storage container create \
            --name "$container" \
            --account-name "$STORAGE_NAME" \
            --account-key "$STORAGE_KEY" \
            --public-access off \
            --output none
        log_success "Created container: $container"
    fi
done

# Generate connection string
CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=${STORAGE_NAME};AccountKey=${STORAGE_KEY};EndpointSuffix=core.windows.net"

# Get endpoints
BLOB_ENDPOINT=$(az storage account show --name "$STORAGE_NAME" --resource-group "$RESOURCE_GROUP" --query "primaryEndpoints.blob" -o tsv)
FILE_ENDPOINT=$(az storage account show --name "$STORAGE_NAME" --resource-group "$RESOURCE_GROUP" --query "primaryEndpoints.file" -o tsv)
QUEUE_ENDPOINT=$(az storage account show --name "$STORAGE_NAME" --resource-group "$RESOURCE_GROUP" --query "primaryEndpoints.queue" -o tsv)
TABLE_ENDPOINT=$(az storage account show --name "$STORAGE_NAME" --resource-group "$RESOURCE_GROUP" --query "primaryEndpoints.table" -o tsv)

# Save deployment info
cat > ".azure-storage-info" << EOF
STORAGE_NAME=$STORAGE_NAME
STORAGE_KEY=$STORAGE_KEY
CONNECTION_STRING=$CONNECTION_STRING
BLOB_ENDPOINT=$BLOB_ENDPOINT
FILE_ENDPOINT=$FILE_ENDPOINT
QUEUE_ENDPOINT=$QUEUE_ENDPOINT
TABLE_ENDPOINT=$TABLE_ENDPOINT
CONTAINERS=${CONTAINERS[*]}
EOF

log_success "Storage Account deployment completed!"
log_info "Connection details saved to .azure-storage-info"
log_warning "Remember to store the storage key securely and remove it from .azure-storage-info if needed"

# Display storage info
log_info "Storage Account Details:"
log_info "  Name: $STORAGE_NAME"
log_info "  SKU: Standard_LRS"
log_info "  Access Tier: Hot"
log_info "  HTTPS Only: Yes"
log_info "  TLS Version: 1.2+"
log_info "  Containers: ${CONTAINERS[*]}"
log_info "  Blob Endpoint: $BLOB_ENDPOINT"
