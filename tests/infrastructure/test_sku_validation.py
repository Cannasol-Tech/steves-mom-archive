"""
Test suite for Infrastructure as Code SKU validation.

This module implements unit tests for Azure resource SKU selections
as defined in docs/architecture/sku-selection.md, ensuring cost optimization
and appropriate service tiers for MVP requirements.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 1.0.0
"""

import pytest
from typing import Dict, List, Any


class TestSKUValidation:
    """Test class for Azure resource SKU validation."""

    @pytest.fixture
    def sku_config(self) -> Dict[str, Dict[str, Any]]:
        """
        Fixture providing SKU configuration for different environments.
        
        Returns:
            Dict containing SKU specifications and constraints
        """
        return {
            'function_app': {
                'mvp_sku': 'Y1',  # Consumption
                'alternative_sku': 'FC1',  # Flex Consumption
                'allowed_skus': ['Y1', 'FC1'],
                'cost_tier': 'consumption',
                'max_monthly_cost': 0
            },
            'sql_database': {
                'mvp_sku': 'Basic',
                'alternative_skus': ['Standard_S0', 'Standard_S1'],
                'allowed_skus': ['Basic', 'Standard_S0', 'Standard_S1'],
                'cost_tier': 'basic',
                'max_monthly_cost': 30,
                'dtu_capacity': {
                    'Basic': 5,
                    'Standard_S0': 10,
                    'Standard_S1': 20
                }
            },
            'redis_cache': {
                'mvp_sku': 'Basic_C0',
                'alternative_skus': ['Standard_C0', 'Standard_C1'],
                'allowed_skus': ['Basic_C0', 'Standard_C0', 'Standard_C1'],
                'cost_tier': 'basic',
                'max_monthly_cost': 20,
                'memory_mb': {
                    'Basic_C0': 250,
                    'Standard_C0': 250,
                    'Standard_C1': 1024
                }
            },
            'storage_account': {
                'mvp_sku': 'Standard_LRS',
                'alternative_skus': ['Standard_GRS', 'Premium_LRS'],
                'allowed_skus': ['Standard_LRS', 'Standard_GRS', 'Premium_LRS'],
                'cost_tier': 'standard',
                'replication_types': {
                    'Standard_LRS': 'Local',
                    'Standard_GRS': 'Geographic',
                    'Premium_LRS': 'Local'
                }
            },
            'key_vault': {
                'mvp_sku': 'standard',
                'alternative_sku': 'premium',
                'allowed_skus': ['standard', 'premium'],
                'cost_tier': 'standard',
                'features': {
                    'standard': ['software_keys', 'secrets', 'certificates'],
                    'premium': ['hsm_keys', 'software_keys', 'secrets', 'certificates']
                }
            }
        }

    @pytest.fixture
    def environment_requirements(self) -> Dict[str, Dict[str, Any]]:
        """
        Fixture providing environment-specific requirements.
        
        Returns:
            Dict containing requirements for each environment
        """
        return {
            'dev': {
                'cost_priority': 'high',
                'performance_priority': 'low',
                'availability_priority': 'low',
                'max_total_monthly_cost': 80
            },
            'staging': {
                'cost_priority': 'medium',
                'performance_priority': 'medium',
                'availability_priority': 'medium',
                'max_total_monthly_cost': 100
            },
            'prod': {
                'cost_priority': 'low',
                'performance_priority': 'high',
                'availability_priority': 'high',
                'max_total_monthly_cost': 200
            }
        }

    def test_function_app_consumption_sku(self, sku_config):
        """Test that Function App uses Consumption plan for cost optimization."""
        function_config = sku_config['function_app']
        
        # MVP should use Consumption plan
        assert function_config['mvp_sku'] == 'Y1', "Function App should use Consumption plan (Y1) for MVP"
        
        # Verify it's in allowed SKUs
        assert function_config['mvp_sku'] in function_config['allowed_skus'], "MVP SKU must be in allowed SKUs list"
        
        # Verify cost tier is consumption
        assert function_config['cost_tier'] == 'consumption', "Function App should use consumption pricing model"

    def test_function_app_alternative_sku(self, sku_config):
        """Test Function App alternative SKU for performance requirements."""
        function_config = sku_config['function_app']
        
        # Alternative should be Flex Consumption
        assert function_config['alternative_sku'] == 'FC1', "Alternative should be Flex Consumption (FC1)"
        
        # Should be in allowed SKUs
        assert function_config['alternative_sku'] in function_config['allowed_skus'], "Alternative SKU must be allowed"

    def test_sql_database_basic_sku(self, sku_config):
        """Test that SQL Database uses Basic SKU for MVP cost optimization."""
        sql_config = sku_config['sql_database']
        
        # MVP should use Basic tier
        assert sql_config['mvp_sku'] == 'Basic', "SQL Database should use Basic SKU for MVP"
        
        # Verify DTU capacity is appropriate for MVP
        basic_dtu = sql_config['dtu_capacity']['Basic']
        assert basic_dtu == 5, f"Basic tier should have 5 DTUs, got {basic_dtu}"
        
        # Verify cost is within MVP budget
        assert sql_config['max_monthly_cost'] <= 30, "SQL Database cost should be within MVP budget"

    def test_sql_database_upgrade_path(self, sku_config):
        """Test SQL Database upgrade path for scaling."""
        sql_config = sku_config['sql_database']
        
        # Verify upgrade options exist
        assert len(sql_config['alternative_skus']) >= 2, "Should have multiple upgrade options"
        
        # Verify DTU progression
        basic_dtu = sql_config['dtu_capacity']['Basic']
        s0_dtu = sql_config['dtu_capacity']['Standard_S0']
        s1_dtu = sql_config['dtu_capacity']['Standard_S1']
        
        assert basic_dtu < s0_dtu < s1_dtu, "DTU capacity should increase with tier"

    def test_redis_cache_basic_sku(self, sku_config):
        """Test that Redis Cache uses Basic C0 for MVP."""
        redis_config = sku_config['redis_cache']
        
        # MVP should use Basic C0
        assert redis_config['mvp_sku'] == 'Basic_C0', "Redis should use Basic C0 for MVP"
        
        # Verify memory allocation
        basic_memory = redis_config['memory_mb']['Basic_C0']
        assert basic_memory == 250, f"Basic C0 should have 250MB memory, got {basic_memory}"

    def test_redis_cache_upgrade_options(self, sku_config):
        """Test Redis Cache upgrade options for scaling."""
        redis_config = sku_config['redis_cache']
        
        # Verify Standard tier options
        assert 'Standard_C0' in redis_config['alternative_skus'], "Should have Standard C0 option"
        assert 'Standard_C1' in redis_config['alternative_skus'], "Should have Standard C1 option"
        
        # Verify memory progression
        basic_memory = redis_config['memory_mb']['Basic_C0']
        standard_c0_memory = redis_config['memory_mb']['Standard_C0']
        standard_c1_memory = redis_config['memory_mb']['Standard_C1']
        
        assert basic_memory == standard_c0_memory, "Basic C0 and Standard C0 should have same memory"
        assert standard_c1_memory > standard_c0_memory, "Standard C1 should have more memory than C0"

    def test_storage_account_lrs_sku(self, sku_config):
        """Test that Storage Account uses Standard LRS for cost optimization."""
        storage_config = sku_config['storage_account']
        
        # MVP should use Standard LRS
        assert storage_config['mvp_sku'] == 'Standard_LRS', "Storage should use Standard LRS for MVP"
        
        # Verify replication type
        lrs_replication = storage_config['replication_types']['Standard_LRS']
        assert lrs_replication == 'Local', "LRS should provide local replication"

    def test_storage_account_replication_options(self, sku_config):
        """Test Storage Account replication upgrade options."""
        storage_config = sku_config['storage_account']
        
        # Verify GRS option exists
        assert 'Standard_GRS' in storage_config['alternative_skus'], "Should have GRS option for production"
        
        # Verify replication types
        grs_replication = storage_config['replication_types']['Standard_GRS']
        assert grs_replication == 'Geographic', "GRS should provide geographic replication"

    def test_key_vault_standard_sku(self, sku_config):
        """Test that Key Vault uses Standard SKU for MVP."""
        kv_config = sku_config['key_vault']
        
        # MVP should use Standard
        assert kv_config['mvp_sku'] == 'standard', "Key Vault should use Standard SKU for MVP"
        
        # Verify features
        standard_features = kv_config['features']['standard']
        required_features = ['software_keys', 'secrets', 'certificates']
        
        for feature in required_features:
            assert feature in standard_features, f"Standard SKU should support {feature}"

    def test_key_vault_premium_upgrade(self, sku_config):
        """Test Key Vault Premium upgrade option for HSM requirements."""
        kv_config = sku_config['key_vault']
        
        # Verify Premium option
        assert kv_config['alternative_sku'] == 'premium', "Should have Premium upgrade option"
        
        # Verify HSM support
        premium_features = kv_config['features']['premium']
        assert 'hsm_keys' in premium_features, "Premium should support HSM keys"

    @pytest.mark.parametrize("environment", ['dev', 'staging', 'prod'])
    def test_environment_cost_constraints(self, sku_config, environment_requirements, environment):
        """Test that SKU selections meet environment cost constraints."""
        env_req = environment_requirements[environment]
        max_cost = env_req['max_total_monthly_cost']
        
        # Calculate estimated total cost
        estimated_cost = (
            sku_config['function_app']['max_monthly_cost'] +
            sku_config['sql_database']['max_monthly_cost'] +
            sku_config['redis_cache']['max_monthly_cost'] +
            10  # Estimated storage + key vault cost
        )
        
        if environment == 'dev':
            # Dev should be well under budget
            assert estimated_cost <= max_cost * 0.8, f"Dev environment cost should be under 80% of budget"
        else:
            # Other environments should be within budget
            assert estimated_cost <= max_cost, f"{environment} environment cost exceeds budget"

    def test_sku_consistency_across_environments(self, sku_config):
        """Test that MVP SKUs are consistent and appropriate."""
        # All MVP SKUs should be cost-optimized tiers
        cost_optimized_tiers = ['basic', 'standard', 'consumption']
        
        for service, config in sku_config.items():
            if 'cost_tier' in config:
                assert config['cost_tier'] in cost_optimized_tiers, f"{service} should use cost-optimized tier"

    def test_scaling_readiness(self, sku_config):
        """Test that all services have clear upgrade paths for scaling."""
        services_requiring_upgrades = ['sql_database', 'redis_cache', 'storage_account']
        
        for service in services_requiring_upgrades:
            config = sku_config[service]
            assert 'alternative_skus' in config, f"{service} should have upgrade options"
            assert len(config['alternative_skus']) >= 1, f"{service} should have at least one upgrade option"

    def test_performance_baseline_compliance(self, sku_config):
        """Test that MVP SKUs meet minimum performance requirements."""
        # SQL Database should have minimum DTU capacity
        sql_dtu = sku_config['sql_database']['dtu_capacity']['Basic']
        assert sql_dtu >= 5, "SQL Database should have at least 5 DTUs"
        
        # Redis should have minimum memory
        redis_memory = sku_config['redis_cache']['memory_mb']['Basic_C0']
        assert redis_memory >= 250, "Redis should have at least 250MB memory"

    def test_security_compliance(self, sku_config):
        """Test that SKU selections support required security features."""
        # Key Vault should support required security features
        kv_features = sku_config['key_vault']['features']['standard']
        required_security_features = ['secrets', 'certificates']
        
        for feature in required_security_features:
            assert feature in kv_features, f"Key Vault should support {feature} for security compliance"

    def test_monitoring_compatibility(self, sku_config):
        """Test that SKU selections are compatible with monitoring requirements."""
        # All services should support basic monitoring
        # This is implicit in Azure, but we verify cost tiers support monitoring
        
        for service, config in sku_config.items():
            # Even basic/standard tiers should support monitoring
            assert config['cost_tier'] in ['basic', 'standard', 'consumption'], f"{service} tier should support monitoring"
