# Behave environment file to auto-skip tagged scenarios
# Scenarios tagged with @skip (or features tagged with @skip) will be marked skipped.

def before_scenario(context, scenario):
    tags = set(getattr(scenario, "tags", []) or [])
    # Skip if scenario or its feature has 'skip' tag
    if "skip" in tags or (hasattr(scenario, "feature") and "skip" in getattr(scenario.feature, "tags", [])):
        scenario.skip("Skipped until functionality is implemented")
