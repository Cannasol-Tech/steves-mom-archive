# Behave environment file to auto-skip tagged scenarios and unimplemented features
# Scenarios or features tagged with @skip will be marked skipped before execution.
# Scenarios for unimplemented features will be automatically skipped.

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.acceptance.features.feature_skip_utils import skip_if_not_implemented


def before_scenario(context, scenario):
    # Check for manual @skip tags
    tags = set(getattr(scenario, "tags", []) or [])
    feature_tags = set(getattr(getattr(scenario, "feature", None), "tags", []) or [])
    if "skip" in tags or "skip" in feature_tags:
        scenario.skip("Skipped until functionality is implemented")

    # Check for unimplemented features and skip automatically
    skip_if_not_implemented(context, scenario)
