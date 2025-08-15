#!/bin/bash

# Validation script for Azure deployment scripts
# This script validates the deployment scripts without actually deploying resources
# 
# Usage: ./validate-deployment-scripts.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

# Check script syntax
validate_script_syntax() {
    local script_file="$1"
    local script_name=$(basename "$script_file")
    
    log_info "Validating syntax: $script_name"
    
    if bash -n "$script_file"; then
        log_success "$script_name - syntax valid"
        return 0
    else
        log_error "$script_name - syntax error"
        return 1
    fi
}

# Check script permissions
validate_script_permissions() {
    local script_file="$1"
    local script_name=$(basename "$script_file")
    
    if [ -x "$script_file" ]; then
        log_success "$script_name - executable"
        return 0
    else
        log_warning "$script_name - not executable"
        return 1
    fi
}

# Validate naming conventions in scripts
validate_naming_conventions() {
    local script_file="$1"
    local script_name=$(basename "$script_file")
    
    log_info "Validating naming conventions: $script_name"
    
    # Check for proper naming patterns
    local naming_patterns=(
        "sql-.*-.*-.*"
        "redis-.*-.*-.*"
        "st.*"
        "kv-.*-.*-.*"
    )
    
    local found_patterns=0
    for pattern in "${naming_patterns[@]}"; do
        if grep -q "$pattern" "$script_file"; then
            ((found_patterns++))
        fi
    done
    
    if [ $found_patterns -gt 0 ]; then
        log_success "$script_name - naming conventions found"
        return 0
    else
        log_warning "$script_name - no naming conventions detected"
        return 1
    fi
}

# Validate required Azure CLI commands
validate_azure_cli_commands() {
    local script_file="$1"
    local script_name=$(basename "$script_file")
    
    log_info "Validating Azure CLI usage: $script_name"
    
    # Check for proper Azure CLI commands based on script type
    if [[ "$script_name" == *"sql"* ]]; then
        if grep -q "az sql server create" "$script_file" && grep -q "az sql db create" "$script_file"; then
            log_success "$script_name - SQL commands found"
        else
            log_warning "$script_name - missing SQL commands"
        fi
    elif [[ "$script_name" == *"redis"* ]]; then
        if grep -q "az redis create" "$script_file"; then
            log_success "$script_name - Redis commands found"
        else
            log_warning "$script_name - missing Redis commands"
        fi
    elif [[ "$script_name" == *"storage"* ]]; then
        if grep -q "az storage account create" "$script_file"; then
            log_success "$script_name - Storage commands found"
        else
            log_warning "$script_name - missing Storage commands"
        fi
    elif [[ "$script_name" == *"keyvault"* ]] || [[ "$script_name" == *"key-vault"* ]]; then
        if grep -q "az keyvault create" "$script_file"; then
            log_success "$script_name - Key Vault commands found"
        else
            log_warning "$script_name - missing Key Vault commands"
        fi
    fi
}

# Validate security configurations
validate_security_settings() {
    local script_file="$1"
    local script_name=$(basename "$script_file")
    
    log_info "Validating security settings: $script_name"
    
    local security_checks=0
    
    # Check for HTTPS/TLS requirements
    if grep -q "https-only\|tls\|ssl" "$script_file"; then
        ((security_checks++))
        log_success "$script_name - HTTPS/TLS settings found"
    fi
    
    # Check for proper access controls
    if grep -q "public-access.*false\|firewall\|access-policy" "$script_file"; then
        ((security_checks++))
        log_success "$script_name - access control settings found"
    fi
    
    if [ $security_checks -eq 0 ]; then
        log_warning "$script_name - no security settings detected"
    fi
}

# Main validation function
main() {
    log_info "Starting deployment script validation..."
    echo
    
    local total_scripts=0
    local valid_scripts=0
    
    # Find all deployment scripts
    for script in "$SCRIPT_DIR"/deploy-*.sh; do
        if [ -f "$script" ]; then
            ((total_scripts++))
            
            echo "----------------------------------------"
            log_info "Validating: $(basename "$script")"
            
            local script_valid=true
            
            # Run all validations
            validate_script_syntax "$script" || script_valid=false
            validate_script_permissions "$script" || script_valid=false
            validate_naming_conventions "$script" || script_valid=false
            validate_azure_cli_commands "$script" || script_valid=false
            validate_security_settings "$script" || script_valid=false
            
            if [ "$script_valid" = true ]; then
                ((valid_scripts++))
                log_success "$(basename "$script") - validation passed"
            else
                log_warning "$(basename "$script") - validation completed with warnings"
            fi
            
            echo
        fi
    done
    
    echo "========================================"
    log_info "Validation Summary:"
    log_info "  Total scripts: $total_scripts"
    log_info "  Valid scripts: $valid_scripts"
    
    if [ $valid_scripts -eq $total_scripts ]; then
        log_success "All deployment scripts validated successfully!"
        return 0
    else
        log_warning "Some scripts have validation warnings"
        return 1
    fi
}

# Run validation
main "$@"
