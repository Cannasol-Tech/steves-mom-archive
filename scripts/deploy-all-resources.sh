#!/bin/bash

# Master deployment script for Steve's Mom AI Chatbot Azure resources
# This script orchestrates the deployment of all Azure resources in the correct order
# 
# Usage: ./deploy-all-resources.sh [environment] [resource-group]
# Example: ./deploy-all-resources.sh dev rg-steves-mom

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT="${1:-dev}"
RESOURCE_GROUP="${2:-rg-steves-mom}"
LOCATION="${3:-eastus}"
PROJECT_NAME="stevesmom"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_header() { echo -e "${CYAN}[DEPLOY]${NC} $1"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check Azure login
    if ! az account show &> /dev/null; then
        log_error "Not logged into Azure. Please run 'az login' first."
        exit 1
    fi
    
    # Check if resource group exists
    if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
        log_error "Resource group '$RESOURCE_GROUP' does not exist."
        log_info "Please create it first or use an existing resource group."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Display deployment plan
show_deployment_plan() {
    log_header "=== DEPLOYMENT PLAN ==="
    log_info "Environment: $ENVIRONMENT"
    log_info "Resource Group: $RESOURCE_GROUP"
    log_info "Location: $LOCATION"
    log_info "Project: $PROJECT_NAME"
    echo
    log_info "Resources to be deployed:"
    log_info "  1. Storage Account (Standard_LRS)"
    log_info "  2. Key Vault (Standard SKU)"
    log_info "  3. SQL Database (Basic tier)"
    log_info "  4. Redis Cache (Basic C0)"
    echo
    log_warning "This deployment will create billable Azure resources."
    log_warning "Estimated monthly cost: \$26-121 (based on MVP SKU selection)"
    echo
}

# Confirm deployment
confirm_deployment() {
    if [ "$ENVIRONMENT" == "prod" ]; then
        log_warning "You are deploying to PRODUCTION environment!"
        echo -n "Are you absolutely sure? Type 'DEPLOY-PROD' to continue: "
        read -r confirmation
        if [ "$confirmation" != "DEPLOY-PROD" ]; then
            log_error "Production deployment cancelled."
            exit 1
        fi
    else
        echo -n "Continue with deployment? (y/N): "
        read -r confirmation
        if [[ ! "$confirmation" =~ ^[Yy]$ ]]; then
            log_error "Deployment cancelled."
            exit 1
        fi
    fi
}

# Deploy resources in dependency order
deploy_resources() {
    local start_time=$(date +%s)
    
    log_header "=== STARTING DEPLOYMENT ==="
    
    # 1. Deploy Storage Account (no dependencies)
    log_header "Step 1/4: Deploying Storage Account..."
    if "$SCRIPT_DIR/deploy-storage-account.sh" "$ENVIRONMENT" "$RESOURCE_GROUP" "$LOCATION"; then
        log_success "Storage Account deployment completed"
    else
        log_error "Storage Account deployment failed"
        exit 1
    fi
    echo
    
    # 2. Deploy Key Vault (no dependencies)
    log_header "Step 2/4: Deploying Key Vault..."
    if "$SCRIPT_DIR/deploy-key-vault.sh" "$ENVIRONMENT" "$RESOURCE_GROUP" "$LOCATION"; then
        log_success "Key Vault deployment completed"
    else
        log_error "Key Vault deployment failed"
        exit 1
    fi
    echo
    
    # 3. Deploy SQL Database (no dependencies)
    log_header "Step 3/4: Deploying SQL Database..."
    if "$SCRIPT_DIR/deploy-sql-database.sh" "$ENVIRONMENT" "$RESOURCE_GROUP" "$LOCATION"; then
        log_success "SQL Database deployment completed"
    else
        log_error "SQL Database deployment failed"
        exit 1
    fi
    echo
    
    # 4. Deploy Redis Cache (no dependencies)
    log_header "Step 4/4: Deploying Redis Cache..."
    if "$SCRIPT_DIR/deploy-redis-cache.sh" "$ENVIRONMENT" "$RESOURCE_GROUP" "$LOCATION"; then
        log_success "Redis Cache deployment completed"
    else
        log_error "Redis Cache deployment failed"
        exit 1
    fi
    echo
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_header "=== DEPLOYMENT COMPLETED ==="
    log_success "All resources deployed successfully in ${duration} seconds!"
}

# Update Key Vault with connection strings
update_key_vault_secrets() {
    log_header "Updating Key Vault with connection strings..."
    
    # Source the deployment info files
    if [ -f ".azure-keyvault-info" ]; then
        source ".azure-keyvault-info"
    else
        log_warning "Key Vault info file not found. Skipping secret updates."
        return
    fi
    
    # Update SQL connection string
    if [ -f ".azure-sql-info" ]; then
        source ".azure-sql-info"
        az keyvault secret set \
            --vault-name "$KEY_VAULT_NAME" \
            --name "sql-connection-string" \
            --value "$CONNECTION_STRING" \
            --output none
        log_success "Updated SQL connection string in Key Vault"
    fi
    
    # Update Redis connection string
    if [ -f ".azure-redis-info" ]; then
        source ".azure-redis-info"
        az keyvault secret set \
            --vault-name "$KEY_VAULT_NAME" \
            --name "redis-connection-string" \
            --value "$CONNECTION_STRING" \
            --output none
        log_success "Updated Redis connection string in Key Vault"
    fi
    
    # Update Storage connection string
    if [ -f ".azure-storage-info" ]; then
        source ".azure-storage-info"
        az keyvault secret set \
            --vault-name "$KEY_VAULT_NAME" \
            --name "storage-connection-string" \
            --value "$CONNECTION_STRING" \
            --output none
        log_success "Updated Storage connection string in Key Vault"
    fi
}

# Generate deployment summary
generate_summary() {
    log_header "=== DEPLOYMENT SUMMARY ==="
    
    echo "Environment: $ENVIRONMENT"
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Location: $LOCATION"
    echo
    
    if [ -f ".azure-storage-info" ]; then
        source ".azure-storage-info"
        echo "Storage Account: $STORAGE_NAME"
    fi
    
    if [ -f ".azure-keyvault-info" ]; then
        source ".azure-keyvault-info"
        echo "Key Vault: $KEY_VAULT_NAME"
    fi
    
    if [ -f ".azure-sql-info" ]; then
        source ".azure-sql-info"
        echo "SQL Server: $SQL_SERVER_NAME"
        echo "SQL Database: $SQL_DATABASE_NAME"
    fi
    
    if [ -f ".azure-redis-info" ]; then
        source ".azure-redis-info"
        echo "Redis Cache: $REDIS_NAME"
    fi
    
    echo
    log_info "Connection details saved to .azure-*-info files"
    log_warning "Remember to:"
    log_warning "  1. Store passwords and keys securely"
    log_warning "  2. Update API keys in Key Vault"
    log_warning "  3. Remove sensitive info from .azure-*-info files if needed"
    log_warning "  4. Set up monitoring and cost alerts"
}

# Main execution
main() {
    log_header "Steve's Mom AI Chatbot - Azure Resource Deployment"
    echo
    
    check_prerequisites
    show_deployment_plan
    confirm_deployment
    deploy_resources
    update_key_vault_secrets
    generate_summary
    
    log_success "Deployment completed successfully!"
    log_info "You can now proceed with Task 1.3: Azure Functions setup"
}

# Run main function
main "$@"
