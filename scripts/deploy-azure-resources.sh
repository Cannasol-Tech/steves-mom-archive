#!/bin/bash

# Azure Resource Deployment Script for Steve's Mom AI Chatbot
# This script deploys Azure resources using the Bicep templates created in Task 1.1
# 
# Prerequisites:
# - Azure CLI installed and logged in
# - Bicep CLI installed
# - Appropriate Azure subscription permissions
#
# Usage: ./deploy-azure-resources.sh [environment] [resource-group-name]
# Example: ./deploy-azure-resources.sh dev rg-steves-mom

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INFRASTRUCTURE_DIR="$PROJECT_ROOT/infrastructure"

# Default values
ENVIRONMENT="${1:-dev}"
RESOURCE_GROUP="${2:-rg-steves-mom}"
LOCATION="${3:-eastus}"
PROJECT_NAME="stevesmom"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check Bicep CLI
    if ! command -v bicep &> /dev/null; then
        log_warning "Bicep CLI not found. Attempting to install via Azure CLI..."
        az bicep install
    fi
    
    # Check Azure login
    if ! az account show &> /dev/null; then
        log_error "Not logged into Azure. Please run 'az login' first."
        exit 1
    fi
    
    # Check if infrastructure directory exists
    if [ ! -d "$INFRASTRUCTURE_DIR" ]; then
        log_error "Infrastructure directory not found: $INFRASTRUCTURE_DIR"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Validate Bicep templates
validate_templates() {
    log_info "Validating Bicep templates..."
    
    # Validate main template
    if [ -f "$INFRASTRUCTURE_DIR/main.bicep" ]; then
        bicep build "$INFRASTRUCTURE_DIR/main.bicep" --stdout > /dev/null
        log_success "Main template validation passed"
    else
        log_error "Main Bicep template not found"
        exit 1
    fi
    
    # Validate modules
    for module in "$INFRASTRUCTURE_DIR/modules"/*.bicep; do
        if [ -f "$module" ]; then
            bicep build "$module" --stdout > /dev/null
            log_success "Module $(basename "$module") validation passed"
        fi
    done
}

# Check if resource group exists
check_resource_group() {
    log_info "Checking resource group: $RESOURCE_GROUP"
    
    if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
        log_success "Resource group $RESOURCE_GROUP exists"
        return 0
    else
        log_warning "Resource group $RESOURCE_GROUP does not exist"
        return 1
    fi
}

# Create resource group if it doesn't exist
create_resource_group() {
    if ! check_resource_group; then
        log_info "Creating resource group: $RESOURCE_GROUP"
        az group create \
            --name "$RESOURCE_GROUP" \
            --location "$LOCATION" \
            --tags \
                Environment="$ENVIRONMENT" \
                Project="$PROJECT_NAME" \
                Owner="cannasol-dev-team" \
                CostCenter="engineering" \
                CreatedBy="deployment-script" \
                CreatedDate="$(date -u +%Y-%m-%d)"
        
        log_success "Resource group created successfully"
    fi
}

# Generate secure password for SQL admin
generate_sql_password() {
    # Generate a secure password that meets Azure SQL requirements
    # At least 8 characters, contains uppercase, lowercase, numbers, and special characters
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-16
}

# Deploy individual resources
deploy_storage_account() {
    log_info "Deploying Storage Account..."
    
    local storage_name="st${PROJECT_NAME}${ENVIRONMENT}${LOCATION}$(openssl rand -hex 3)"
    
    az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --template-file "$INFRASTRUCTURE_DIR/modules/storage.bicep" \
        --parameters \
            storageAccountName="$storage_name" \
            location="$LOCATION" \
            environment="$ENVIRONMENT" \
            tags="{\"Environment\":\"$ENVIRONMENT\",\"Project\":\"$PROJECT_NAME\"}"
    
    log_success "Storage Account deployed: $storage_name"
    echo "$storage_name" > "$PROJECT_ROOT/.azure-storage-name"
}

deploy_key_vault() {
    log_info "Deploying Key Vault..."
    
    local kv_name="kv-${PROJECT_NAME}-${ENVIRONMENT}-${LOCATION}"
    
    az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --template-file "$INFRASTRUCTURE_DIR/modules/keyvault.bicep" \
        --parameters \
            keyVaultName="$kv_name" \
            location="$LOCATION" \
            environment="$ENVIRONMENT" \
            tags="{\"Environment\":\"$ENVIRONMENT\",\"Project\":\"$PROJECT_NAME\"}"
    
    log_success "Key Vault deployed: $kv_name"
    echo "$kv_name" > "$PROJECT_ROOT/.azure-keyvault-name"
}

deploy_sql_database() {
    log_info "Deploying SQL Database..."
    
    local sql_server_name="sql-${PROJECT_NAME}-${ENVIRONMENT}-${LOCATION}"
    local sql_db_name="sqldb-${PROJECT_NAME}-${ENVIRONMENT}"
    local sql_admin_username="stevesmomadmin"
    local sql_admin_password
    
    # Generate secure password
    sql_admin_password=$(generate_sql_password)
    
    az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --template-file "$INFRASTRUCTURE_DIR/modules/sql.bicep" \
        --parameters \
            sqlServerName="$sql_server_name" \
            sqlDatabaseName="$sql_db_name" \
            location="$LOCATION" \
            environment="$ENVIRONMENT" \
            adminUsername="$sql_admin_username" \
            adminPassword="$sql_admin_password" \
            tags="{\"Environment\":\"$ENVIRONMENT\",\"Project\":\"$PROJECT_NAME\"}"
    
    log_success "SQL Database deployed: $sql_server_name/$sql_db_name"
    
    # Store connection info securely
    echo "$sql_server_name" > "$PROJECT_ROOT/.azure-sql-server"
    echo "$sql_db_name" > "$PROJECT_ROOT/.azure-sql-database"
    echo "$sql_admin_username" > "$PROJECT_ROOT/.azure-sql-username"
    
    log_warning "SQL Admin password generated. Store it securely: $sql_admin_password"
}

deploy_redis_cache() {
    log_info "Deploying Redis Cache..."
    
    local redis_name="redis-${PROJECT_NAME}-${ENVIRONMENT}-${LOCATION}"
    
    az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --template-file "$INFRASTRUCTURE_DIR/modules/redis.bicep" \
        --parameters \
            redisCacheName="$redis_name" \
            location="$LOCATION" \
            environment="$ENVIRONMENT" \
            tags="{\"Environment\":\"$ENVIRONMENT\",\"Project\":\"$PROJECT_NAME\"}"
    
    log_success "Redis Cache deployed: $redis_name"
    echo "$redis_name" > "$PROJECT_ROOT/.azure-redis-name"
}

# Main deployment function
main() {
    log_info "Starting Azure resource deployment for Steve's Mom AI Chatbot"
    log_info "Environment: $ENVIRONMENT"
    log_info "Resource Group: $RESOURCE_GROUP"
    log_info "Location: $LOCATION"
    
    # Run deployment steps
    check_prerequisites
    validate_templates
    create_resource_group
    
    # Deploy resources in dependency order
    deploy_storage_account
    deploy_key_vault
    deploy_sql_database
    deploy_redis_cache
    
    log_success "All Azure resources deployed successfully!"
    log_info "Resource names have been saved to .azure-* files in the project root"
    log_warning "Remember to store the SQL admin password securely"
}

# Run main function
main "$@"
