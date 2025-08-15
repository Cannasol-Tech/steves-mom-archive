#!/bin/bash

# Deploy Azure Redis Cache for Steve's Mom AI Chatbot
# Usage: ./deploy-redis-cache.sh [environment] [resource-group]

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
REDIS_NAME="redis-${PROJECT_NAME}-${ENVIRONMENT}-${LOCATION}"

log_info "Deploying Redis Cache..."
log_info "Name: $REDIS_NAME"
log_info "Resource Group: $RESOURCE_GROUP"
log_info "SKU: Basic C0 (250MB)"

# Check if Redis Cache already exists
if az redis show --name "$REDIS_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    log_warning "Redis Cache $REDIS_NAME already exists. Skipping creation."
else
    log_info "Creating Redis Cache (this may take several minutes)..."
    az redis create \
        --name "$REDIS_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --sku "Basic" \
        --vm-size "C0" \
        --enable-non-ssl-port false \
        --minimum-tls-version "1.2" \
        --tags \
            Environment="$ENVIRONMENT" \
            Project="$PROJECT_NAME" \
            Owner="cannasol-dev-team" \
            CostCenter="engineering" \
            CreatedBy="deployment-script"
    
    log_success "Redis Cache created successfully"
fi

# Get Redis connection details
log_info "Retrieving connection details..."
REDIS_HOSTNAME=$(az redis show --name "$REDIS_NAME" --resource-group "$RESOURCE_GROUP" --query "hostName" -o tsv)
REDIS_SSL_PORT=$(az redis show --name "$REDIS_NAME" --resource-group "$RESOURCE_GROUP" --query "sslPort" -o tsv)
REDIS_PRIMARY_KEY=$(az redis list-keys --name "$REDIS_NAME" --resource-group "$RESOURCE_GROUP" --query "primaryKey" -o tsv)

# Generate connection string
CONNECTION_STRING="${REDIS_HOSTNAME}:${REDIS_SSL_PORT},password=${REDIS_PRIMARY_KEY},ssl=True,abortConnect=False"

# Save deployment info
cat > ".azure-redis-info" << EOF
REDIS_NAME=$REDIS_NAME
REDIS_HOSTNAME=$REDIS_HOSTNAME
REDIS_SSL_PORT=$REDIS_SSL_PORT
REDIS_PRIMARY_KEY=$REDIS_PRIMARY_KEY
CONNECTION_STRING=$CONNECTION_STRING
EOF

log_success "Redis Cache deployment completed!"
log_info "Connection details saved to .azure-redis-info"
log_warning "Remember to store the primary key securely and remove it from .azure-redis-info if needed"

# Display connection info
log_info "Redis Cache Details:"
log_info "  Hostname: $REDIS_HOSTNAME"
log_info "  SSL Port: $REDIS_SSL_PORT"
log_info "  Memory: 250MB (Basic C0)"
log_info "  SSL Required: Yes"
log_info "  TLS Version: 1.2+"
