# Behave environment file to auto-skip tagged scenarios
# Scenarios or features tagged with @skip will be marked skipped before execution.

def before_scenario(context, scenario):
    tags = set(getattr(scenario, "tags", []) or [])
    feature_tags = set(getattr(getattr(scenario, "feature", None), "tags", []) or [])
    if "skip" in tags or "skip" in feature_tags:
        scenario.skip("Skipped until functionality is implemented")
