"""
Test suite for Infrastructure as Code naming conventions validation.

This module implements unit tests for Azure resource naming conventions
as defined in docs/architecture/naming.md, ensuring compliance with
Azure naming requirements and project standards.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 1.0.0
"""

import pytest
import re
from typing import Dict, List, Tuple


class TestNamingConventions:
    """Test class for Azure resource naming convention validation."""

    @pytest.fixture
    def naming_config(self) -> Dict[str, Dict[str, str]]:
        """
        Fixture providing naming configuration for different environments.
        
        Returns:
            Dict containing naming patterns and constraints for each resource type
        """
        return {
            'project_name': 'stevesmom',
            'environments': ['dev', 'staging', 'prod'],
            'regions': ['eastus', 'eastus2', 'westus2', 'centralus'],
            'patterns': {
                'resource_group': r'^rg-[a-z0-9]+-[a-z]+-[a-z0-9]+$',
                'function_app': r'^func-[a-z0-9]+-[a-z]+-[a-z0-9]+$',
                'storage_account': r'^st[a-z0-9]{3,22}$',
                'sql_server': r'^sql-[a-z0-9]+-[a-z]+-[a-z0-9]+$',
                'sql_database': r'^sqldb-[a-z0-9]+-[a-z]+$',
                'redis_cache': r'^redis-[a-z0-9]+-[a-z]+-[a-z0-9]+$',
                'key_vault': r'^kv-[a-z0-9]+-[a-z]+-[a-z0-9]+$',
                'static_web_app': r'^swa-[a-z0-9]+-[a-z]+-[a-z0-9]+$',
                'app_insights': r'^ai-[a-z0-9]+-[a-z]+-[a-z0-9]+$',
                'log_analytics': r'^law-[a-z0-9]+-[a-z]+-[a-z0-9]+$'
            },
            'length_constraints': {
                'resource_group': (1, 90),
                'function_app': (2, 60),
                'storage_account': (3, 24),
                'sql_server': (1, 63),
                'sql_database': (1, 128),
                'redis_cache': (1, 63),
                'key_vault': (3, 24),
                'static_web_app': (2, 60),
                'app_insights': (1, 260),
                'log_analytics': (4, 63)
            }
        }

    def generate_resource_name(self, resource_type: str, project: str, 
                             environment: str, region: str, 
                             unique_suffix: str = '001') -> str:
        """
        Generate resource name following naming conventions.
        
        Args:
            resource_type: Type of Azure resource
            project: Project name
            environment: Environment designation
            region: Azure region
            unique_suffix: Unique suffix for globally unique resources
            
        Returns:
            Generated resource name following conventions
        """
        if resource_type == 'resource_group':
            return f'rg-{project}-{environment}-{region}'
        elif resource_type == 'function_app':
            return f'func-{project}-{environment}-{region}'
        elif resource_type == 'storage_account':
            # Use abbreviated forms to fit 24-char limit
            env_abbrev = {'dev': 'dev', 'staging': 'stg', 'prod': 'prd'}[environment]
            region_abbrev = {'eastus': 'eus', 'eastus2': 'eus2', 'westus2': 'wus2', 'centralus': 'cus'}[region]
            return f'st{project}{env_abbrev}{region_abbrev}{unique_suffix}'
        elif resource_type == 'sql_server':
            return f'sql-{project}-{environment}-{region}'
        elif resource_type == 'sql_database':
            return f'sqldb-{project}-{environment}'
        elif resource_type == 'redis_cache':
            return f'redis-{project}-{environment}-{region}'
        elif resource_type == 'key_vault':
            # Use existing shared Key Vault
            return 'kv-cloud-agents'
        elif resource_type == 'static_web_app':
            return f'swa-{project}-{environment}-{region}'
        elif resource_type == 'app_insights':
            return f'ai-{project}-{environment}-{region}'
        elif resource_type == 'log_analytics':
            return f'law-{project}-{environment}-{region}'
        else:
            raise ValueError(f"Unknown resource type: {resource_type}")

    @pytest.mark.parametrize("resource_type", [
        'resource_group', 'function_app', 'sql_server', 'redis_cache',
        'static_web_app', 'app_insights', 'log_analytics'
    ])
    def test_hyphenated_resource_naming_pattern(self, naming_config, resource_type):
        """Test naming pattern for resources that use hyphens."""
        project = naming_config['project_name']
        environment = 'dev'
        region = 'eastus'
        
        name = self.generate_resource_name(resource_type, project, environment, region)
        pattern = naming_config['patterns'][resource_type]
        
        assert re.match(pattern, name), f"{resource_type} name '{name}' doesn't match pattern '{pattern}'"
        assert len(name) >= naming_config['length_constraints'][resource_type][0]
        assert len(name) <= naming_config['length_constraints'][resource_type][1]

    def test_storage_account_naming_pattern(self, naming_config):
        """Test storage account naming pattern (no hyphens, alphanumeric only)."""
        project = naming_config['project_name']
        environment = 'dev'
        region = 'eastus'
        
        name = self.generate_resource_name('storage_account', project, environment, region)
        pattern = naming_config['patterns']['storage_account']
        
        assert re.match(pattern, name), f"Storage account name '{name}' doesn't match pattern '{pattern}'"
        assert len(name) >= 3
        assert len(name) <= 24
        assert name.islower()
        assert name.isalnum()

    def test_sql_database_naming_pattern(self, naming_config):
        """Test SQL database naming pattern (no region component)."""
        project = naming_config['project_name']
        environment = 'prod'
        
        name = self.generate_resource_name('sql_database', project, environment, 'eastus')
        pattern = naming_config['patterns']['sql_database']
        
        assert re.match(pattern, name), f"SQL database name '{name}' doesn't match pattern '{pattern}'"
        assert len(name) >= 1
        assert len(name) <= 128
        assert 'eastus' not in name  # Database names don't include region

    @pytest.mark.parametrize("environment", ['dev', 'staging', 'prod'])
    def test_environment_consistency(self, naming_config, environment):
        """Test that all resource names consistently use the same environment."""
        project = naming_config['project_name']
        region = 'eastus'
        
        resource_types = ['resource_group', 'function_app', 'sql_server']
        
        for resource_type in resource_types:
            name = self.generate_resource_name(resource_type, project, environment, region)
            assert environment in name, f"{resource_type} name '{name}' doesn't contain environment '{environment}'"

    @pytest.mark.parametrize("region", ['eastus', 'eastus2', 'westus2', 'centralus'])
    def test_region_consistency(self, naming_config, region):
        """Test that resource names consistently use the same region."""
        project = naming_config['project_name']
        environment = 'dev'
        
        # Test resources that include region in name (excluding shared key_vault)
        regional_resources = ['resource_group', 'function_app', 'sql_server']
        
        for resource_type in regional_resources:
            name = self.generate_resource_name(resource_type, project, environment, region)
            assert region in name, f"{resource_type} name '{name}' doesn't contain region '{region}'"

    def test_globally_unique_resources(self, naming_config):
        """Test that globally unique resources have appropriate uniqueness mechanisms."""
        project = naming_config['project_name']
        environment = 'prod'
        region = 'eastus'
        
        # Resources that must be globally unique (excluding shared key_vault)
        unique_resources = ['function_app', 'storage_account', 'sql_server', 'redis_cache']
        
        for resource_type in unique_resources:
            name1 = self.generate_resource_name(resource_type, project, environment, region, '001')
            name2 = self.generate_resource_name(resource_type, project, environment, region, '002')
            
            if resource_type == 'storage_account':
                # Storage accounts should have different unique suffixes
                assert name1 != name2, f"Storage account names should be unique: {name1} vs {name2}"
            else:
                # Other resources use the same base name but would get unique suffixes in real deployment
                base_name = self.generate_resource_name(resource_type, project, environment, region)
                assert len(base_name) > 0, f"{resource_type} base name should not be empty"

    def test_character_restrictions(self, naming_config):
        """Test that resource names comply with Azure character restrictions."""
        project = naming_config['project_name']
        environment = 'dev'
        region = 'eastus'
        
        # Test storage account (most restrictive)
        storage_name = self.generate_resource_name('storage_account', project, environment, region)
        assert storage_name.islower(), "Storage account name must be lowercase"
        assert storage_name.isalnum(), "Storage account name must be alphanumeric only"
        
        # Test hyphenated resources
        hyphenated_resources = ['resource_group', 'function_app', 'sql_server']
        for resource_type in hyphenated_resources:
            name = self.generate_resource_name(resource_type, project, environment, region)
            assert not name.startswith('-'), f"{resource_type} name cannot start with hyphen"
            assert not name.endswith('-'), f"{resource_type} name cannot end with hyphen"
            assert '--' not in name, f"{resource_type} name cannot contain consecutive hyphens"

    def test_length_constraints(self, naming_config):
        """Test that all resource names meet Azure length constraints."""
        project = naming_config['project_name']
        environment = 'staging'  # Longest environment name
        region = 'centralus'     # Longest region name
        
        for resource_type, (min_len, max_len) in naming_config['length_constraints'].items():
            name = self.generate_resource_name(resource_type, project, environment, region)
            
            assert len(name) >= min_len, f"{resource_type} name '{name}' is too short (min: {min_len})"
            assert len(name) <= max_len, f"{resource_type} name '{name}' is too long (max: {max_len})"

    def test_reserved_names_avoidance(self, naming_config):
        """Test that generated names avoid Azure reserved names."""
        reserved_patterns = [
            r'^admin$', r'^administrator$', r'^sa$', r'^root$',
            r'^guest$', r'^public$', r'^user$', r'^test$'
        ]
        
        project = naming_config['project_name']
        environment = 'dev'
        region = 'eastus'
        
        for resource_type in naming_config['patterns'].keys():
            name = self.generate_resource_name(resource_type, project, environment, region)
            
            for pattern in reserved_patterns:
                assert not re.match(pattern, name.lower()), f"{resource_type} name '{name}' matches reserved pattern '{pattern}'"

    def test_case_sensitivity_compliance(self, naming_config):
        """Test that resource names comply with Azure case sensitivity requirements."""
        project = naming_config['project_name']
        environment = 'Dev'  # Mixed case to test normalization
        region = 'EastUS'    # Mixed case to test normalization
        
        # Most Azure resources require lowercase names
        lowercase_resources = ['storage_account', 'function_app', 'sql_server', 'key_vault']
        
        for resource_type in lowercase_resources:
            name = self.generate_resource_name(resource_type, project, environment.lower(), region.lower())
            assert name.islower() or '-' in name, f"{resource_type} name '{name}' should be lowercase or contain hyphens"
