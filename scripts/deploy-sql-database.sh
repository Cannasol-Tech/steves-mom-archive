#!/bin/bash

# Deploy Azure SQL Database for Steve's Mom AI Chatbot
# Usage: ./deploy-sql-database.sh [environment] [resource-group]

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
SQL_SERVER_NAME="sql-${PROJECT_NAME}-${ENVIRONMENT}-${LOCATION}"
SQL_DATABASE_NAME="sqldb-${PROJECT_NAME}-${ENVIRONMENT}"
SQL_ADMIN_USERNAME="stevesmomadmin"

# Generate secure password if not provided
if [ -z "$SQL_ADMIN_PASSWORD" ]; then
    log_info "Generating secure SQL admin password..."
    SQL_ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-16)
    log_warning "Generated password: $SQL_ADMIN_PASSWORD"
    log_warning "Please store this password securely!"
fi

log_info "Deploying SQL Database..."
log_info "Server: $SQL_SERVER_NAME"
log_info "Database: $SQL_DATABASE_NAME"
log_info "Resource Group: $RESOURCE_GROUP"

# Check if SQL Server already exists
if az sql server show --name "$SQL_SERVER_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    log_warning "SQL Server $SQL_SERVER_NAME already exists. Skipping server creation."
else
    log_info "Creating SQL Server..."
    az sql server create \
        --name "$SQL_SERVER_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --admin-user "$SQL_ADMIN_USERNAME" \
        --admin-password "$SQL_ADMIN_PASSWORD" \
        --enable-public-network true \
        --minimal-tls-version "1.2" \
        --tags \
            Environment="$ENVIRONMENT" \
            Project="$PROJECT_NAME" \
            Owner="cannasol-dev-team" \
            CostCenter="engineering" \
            CreatedBy="deployment-script"
    
    log_success "SQL Server created successfully"
fi

# Configure firewall rules
log_info "Configuring firewall rules..."

# Allow Azure services
az sql server firewall-rule create \
    --resource-group "$RESOURCE_GROUP" \
    --server "$SQL_SERVER_NAME" \
    --name "AllowAzureServices" \
    --start-ip-address "0.0.0.0" \
    --end-ip-address "0.0.0.0" \
    --output none 2>/dev/null || log_warning "Firewall rule may already exist"

log_success "Firewall rules configured"

# Check if database already exists
if az sql db show --name "$SQL_DATABASE_NAME" --server "$SQL_SERVER_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    log_warning "Database $SQL_DATABASE_NAME already exists. Skipping database creation."
else
    log_info "Creating SQL Database..."
    az sql db create \
        --name "$SQL_DATABASE_NAME" \
        --server "$SQL_SERVER_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --service-objective "Basic" \
        --max-size "2GB" \
        --collation "SQL_Latin1_General_CP1_CI_AS" \
        --backup-storage-redundancy "Local" \
        --tags \
            Environment="$ENVIRONMENT" \
            Project="$PROJECT_NAME" \
            Owner="cannasol-dev-team" \
            CostCenter="engineering" \
            CreatedBy="deployment-script"
    
    log_success "SQL Database created successfully"
fi

# Get connection string
log_info "Generating connection string..."
CONNECTION_STRING="Server=tcp:${SQL_SERVER_NAME}.database.windows.net,1433;Initial Catalog=${SQL_DATABASE_NAME};Persist Security Info=False;User ID=${SQL_ADMIN_USERNAME};Password=${SQL_ADMIN_PASSWORD};MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"

# Save deployment info
cat > ".azure-sql-info" << EOF
SQL_SERVER_NAME=$SQL_SERVER_NAME
SQL_DATABASE_NAME=$SQL_DATABASE_NAME
SQL_ADMIN_USERNAME=$SQL_ADMIN_USERNAME
SQL_ADMIN_PASSWORD=$SQL_ADMIN_PASSWORD
CONNECTION_STRING=$CONNECTION_STRING
EOF

log_success "SQL Database deployment completed!"
log_info "Connection details saved to .azure-sql-info"
log_warning "Remember to store the admin password securely and remove it from .azure-sql-info if needed"

# Test connection (optional)
if command -v sqlcmd &> /dev/null; then
    log_info "Testing connection..."
    if sqlcmd -S "${SQL_SERVER_NAME}.database.windows.net" -d "$SQL_DATABASE_NAME" -U "$SQL_ADMIN_USERNAME" -P "$SQL_ADMIN_PASSWORD" -Q "SELECT 1 as test" &>/dev/null; then
        log_success "Connection test successful"
    else
        log_warning "Connection test failed - this may be normal if sqlcmd is not configured properly"
    fi
else
    log_info "sqlcmd not available - skipping connection test"
fi
