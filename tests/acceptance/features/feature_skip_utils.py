"""
Feature Skip Utilities for Acceptance Tests

This module provides utilities for automatically skipping unimplemented
features in acceptance tests based on the feature registry.
"""
import re
from typing import Optional
from backend.features.feature_registry import should_skip_feature, get_skip_reason


def extract_feature_id_from_scenario(scenario) -> Optional[str]:
    """Extract feature ID from scenario name or tags."""
    # Check scenario name for FR-X.Y pattern
    name_match = re.search(r'FR-\d+\.\d+', scenario.name)
    if name_match:
        return name_match.group(0)
    
    # Check tags for FR-X.Y pattern
    for tag in scenario.tags:
        tag_match = re.search(r'FR-\d+\.\d+', tag)
        if tag_match:
            return tag_match.group(0)
    
    return None


def skip_if_not_implemented(context, scenario):
    """Skip scenario if the associated feature is not implemented."""
    feature_id = extract_feature_id_from_scenario(scenario)

    if not feature_id:
        # No feature ID found, let the test run
        return

    if should_skip_feature(feature_id):
        reason = get_skip_reason(feature_id)
        scenario.skip(f"Skipping {feature_id}: {reason}")


def check_feature_implementation(feature_id: str) -> bool:
    """Check if a feature is implemented."""
    return not should_skip_feature(feature_id)


def get_implementation_status(feature_id: str) -> str:
    """Get implementation status message for a feature."""
    if should_skip_feature(feature_id):
        return f"❌ {feature_id}: {get_skip_reason(feature_id)}"
    else:
        return f"✅ {feature_id}: Implemented"


# Behave hook functions
def before_scenario(context, scenario):
    """Behave hook to check feature implementation before each scenario."""
    # Skip scenarios for unimplemented features
    skip_if_not_implemented(context, scenario)


def before_feature(context, feature):
    """Behave hook to run before each feature."""
    # You can add feature-level setup here if needed
    pass


def after_scenario(context, scenario):
    """Behave hook to run after each scenario."""
    # You can add scenario cleanup here if needed
    pass
