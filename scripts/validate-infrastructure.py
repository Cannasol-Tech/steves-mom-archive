#!/usr/bin/env python3
"""
Infrastructure validation script for Steve's Mom AI Chatbot.

This script validates Bicep templates for naming conventions, SKU selections,
and Azure best practices before deployment.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 1.0.0
"""

import os
import sys
import json
import subprocess
import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class InfrastructureValidator:
    """Validates infrastructure templates and configurations."""

    def __init__(self, infrastructure_path: str = "infrastructure"):
        """
        Initialize the validator.
        
        Args:
            infrastructure_path: Path to infrastructure templates
        """
        self.infrastructure_path = Path(infrastructure_path)
        self.errors = []
        self.warnings = []
        
    def validate_all(self) -> bool:
        """
        Run all validation checks.
        
        Returns:
            True if all validations pass, False otherwise
        """
        print("🔍 Starting infrastructure validation...")
        
        # Check if infrastructure directory exists
        if not self.infrastructure_path.exists():
            self.errors.append(f"Infrastructure directory not found: {self.infrastructure_path}")
            return False
            
        # Run validation checks
        self.validate_bicep_syntax()
        self.validate_naming_conventions()
        self.validate_sku_selections()
        self.validate_security_settings()
        self.validate_tags()
        self.validate_dependencies()
        
        # Report results
        self.report_results()
        
        return len(self.errors) == 0

    def validate_bicep_syntax(self) -> None:
        """Validate Bicep template syntax using Azure CLI."""
        print("📝 Validating Bicep syntax...")
        
        bicep_files = list(self.infrastructure_path.rglob("*.bicep"))
        
        if not bicep_files:
            self.warnings.append("No Bicep files found for syntax validation")
            return
            
        for bicep_file in bicep_files:
            try:
                # Use bicep build to validate syntax
                result = subprocess.run(
                    ["bicep", "build", str(bicep_file), "--stdout"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    self.errors.append(f"Bicep syntax error in {bicep_file}: {result.stderr}")
                else:
                    print(f"  ✅ {bicep_file.name} - syntax valid")
                    
            except subprocess.TimeoutExpired:
                self.errors.append(f"Bicep validation timeout for {bicep_file}")
            except FileNotFoundError:
                self.warnings.append("Bicep CLI not found - skipping syntax validation")
                break

    def validate_naming_conventions(self) -> None:
        """Validate resource naming conventions."""
        print("🏷️  Validating naming conventions...")
        
        naming_patterns = {
            'resource_group': r'rg-[a-z0-9]+-[a-z]+-[a-z0-9]+',
            'function_app': r'func-[a-z0-9]+-[a-z]+-[a-z0-9]+',
            'storage_account': r'st[a-z0-9]{3,22}',
            'sql_server': r'sql-[a-z0-9]+-[a-z]+-[a-z0-9]+',
            'key_vault': r'kv-[a-z0-9]+-[a-z]+-[a-z0-9]+',
        }
        
        # Read main.bicep to extract naming variables
        main_bicep = self.infrastructure_path / "main.bicep"
        if not main_bicep.exists():
            self.errors.append("main.bicep not found")
            return
            
        with open(main_bicep, 'r') as f:
            content = f.read()
            
        # Extract naming variable definitions
        naming_section = self._extract_naming_section(content)
        
        for resource_type, pattern in naming_patterns.items():
            if resource_type in naming_section:
                name_template = naming_section[resource_type]
                if not self._validate_naming_pattern(name_template, pattern):
                    self.errors.append(f"Naming pattern violation for {resource_type}: {name_template}")
                else:
                    print(f"  ✅ {resource_type} - naming convention valid")

    def validate_sku_selections(self) -> None:
        """Validate SKU selections against cost optimization requirements."""
        print("💰 Validating SKU selections...")
        
        expected_skus = {
            'function_app': ['Y1', 'FC1'],  # Consumption or Flex Consumption
            'sql_database': ['Basic', 'Standard'],
            'redis_cache': ['Basic_C0', 'Standard_C0'],
            'storage_account': ['Standard_LRS', 'Standard_GRS'],
            'key_vault': ['standard', 'premium']
        }
        
        # Check module files for SKU configurations
        modules_path = self.infrastructure_path / "modules"
        if not modules_path.exists():
            self.warnings.append("Modules directory not found")
            return
            
        for module_file in modules_path.glob("*.bicep"):
            self._validate_module_skus(module_file, expected_skus)

    def validate_security_settings(self) -> None:
        """Validate security configurations."""
        print("🔒 Validating security settings...")
        
        security_checks = [
            ('minimalTlsVersion', '1.2'),
            ('supportsHttpsTrafficOnly', 'true'),
            ('enableSoftDelete', 'true'),
            ('publicNetworkAccess', 'Enabled')  # Acceptable for MVP
        ]
        
        modules_path = self.infrastructure_path / "modules"
        if modules_path.exists():
            for module_file in modules_path.glob("*.bicep"):
                self._validate_module_security(module_file, security_checks)

    def validate_tags(self) -> None:
        """Validate required tags are present."""
        print("🏷️  Validating resource tags...")
        
        required_tags = ['Environment', 'Project', 'Owner', 'CostCenter', 'CreatedBy']
        
        main_bicep = self.infrastructure_path / "main.bicep"
        if main_bicep.exists():
            with open(main_bicep, 'r') as f:
                content = f.read()
                
            # Check if commonTags variable includes required tags
            if 'commonTags' in content:
                for tag in required_tags:
                    if tag not in content:
                        self.warnings.append(f"Required tag '{tag}' not found in commonTags")
                    else:
                        print(f"  ✅ {tag} - tag present")

    def validate_dependencies(self) -> None:
        """Validate module dependencies."""
        print("🔗 Validating module dependencies...")
        
        main_bicep = self.infrastructure_path / "main.bicep"
        if not main_bicep.exists():
            return
            
        with open(main_bicep, 'r') as f:
            content = f.read()
            
        # Check for proper dependsOn declarations
        dependency_patterns = [
            (r'module functionApp.*dependsOn.*storage', "Function App should depend on Storage"),
            (r'module functionApp.*dependsOn.*keyVault', "Function App should depend on Key Vault")
        ]
        
        for pattern, description in dependency_patterns:
            if not re.search(pattern, content, re.DOTALL | re.IGNORECASE):
                self.warnings.append(f"Missing dependency: {description}")
            else:
                print(f"  ✅ {description}")

    def _extract_naming_section(self, content: str) -> Dict[str, str]:
        """Extract naming variable definitions from Bicep content."""
        naming_section = {}
        
        # Look for naming variable definition
        naming_match = re.search(r'var naming = \{([^}]+)\}', content, re.DOTALL)
        if naming_match:
            naming_content = naming_match.group(1)
            
            # Extract individual naming patterns
            pattern_matches = re.findall(r'(\w+):\s*[\'"]([^\'"]+)[\'"]', naming_content)
            for key, value in pattern_matches:
                naming_section[key] = value
                
        return naming_section

    def _validate_naming_pattern(self, template: str, expected_pattern: str) -> bool:
        """Validate a naming template against expected pattern."""
        # Replace Bicep variables with sample values for pattern matching
        sample_template = template.replace('${projectName}', 'stevesmom')
        sample_template = sample_template.replace('${environment}', 'dev')
        sample_template = sample_template.replace('${location}', 'eastus')
        sample_template = re.sub(r'\$\{[^}]+\}', '001', sample_template)
        
        return bool(re.match(expected_pattern, sample_template))

    def _validate_module_skus(self, module_file: Path, expected_skus: Dict[str, List[str]]) -> None:
        """Validate SKUs in a specific module file."""
        with open(module_file, 'r') as f:
            content = f.read()
            
        module_name = module_file.stem
        
        # Check for SKU definitions
        sku_matches = re.findall(r'sku:\s*[\'"]?([^\s\'"]+)[\'"]?', content)
        
        for sku in sku_matches:
            # Determine which service this SKU belongs to
            service_type = self._determine_service_type(module_name, content)
            
            if service_type in expected_skus:
                if sku not in expected_skus[service_type]:
                    self.warnings.append(f"Unexpected SKU '{sku}' in {module_file.name} for {service_type}")
                else:
                    print(f"  ✅ {service_type} - SKU '{sku}' is approved")

    def _validate_module_security(self, module_file: Path, security_checks: List[Tuple[str, str]]) -> None:
        """Validate security settings in a module file."""
        with open(module_file, 'r') as f:
            content = f.read()
            
        for setting, expected_value in security_checks:
            if setting in content:
                # Check if the setting has the expected value
                pattern = f'{setting}:\\s*{expected_value}'
                if re.search(pattern, content):
                    print(f"  ✅ {module_file.name} - {setting} correctly configured")
                else:
                    self.warnings.append(f"Security setting '{setting}' may not be correctly configured in {module_file.name}")

    def _determine_service_type(self, module_name: str, content: str) -> str:
        """Determine the Azure service type from module name and content."""
        if 'function' in module_name.lower():
            return 'function_app'
        elif 'sql' in module_name.lower():
            return 'sql_database'
        elif 'redis' in module_name.lower():
            return 'redis_cache'
        elif 'storage' in module_name.lower():
            return 'storage_account'
        elif 'keyvault' in module_name.lower() or 'kv' in module_name.lower():
            return 'key_vault'
        else:
            return 'unknown'

    def report_results(self) -> None:
        """Report validation results."""
        print("\n" + "="*60)
        print("📊 VALIDATION RESULTS")
        print("="*60)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
                
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
                
        if not self.errors and not self.warnings:
            print("\n✅ All validations passed!")
        elif not self.errors:
            print(f"\n✅ Validation passed with {len(self.warnings)} warnings")
        else:
            print(f"\n❌ Validation failed with {len(self.errors)} errors and {len(self.warnings)} warnings")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate infrastructure templates")
    parser.add_argument(
        "--infrastructure-path",
        default="infrastructure",
        help="Path to infrastructure templates (default: infrastructure)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors"
    )
    
    args = parser.parse_args()
    
    validator = InfrastructureValidator(args.infrastructure_path)
    success = validator.validate_all()
    
    if args.strict and validator.warnings:
        print("\n❌ Strict mode: treating warnings as errors")
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
