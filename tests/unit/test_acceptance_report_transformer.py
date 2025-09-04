import types

# Import the function under test from the script
from scripts.acceptance_to_executive_report import summarize_behave


def test_summarize_behave_marks_skip_scenarios_as_skipped():
    # Minimal Behave-like JSON with a feature and one scenario tagged with @skip
    behave_json = [
        {
            "name": "Feature: Placeholder",
            "tags": ["@prd-1"],
            "elements": [
                {
                    "type": "scenario",
                    "name": "Scenario: Placeholder acceptance",
                    "tags": ["@skip", "@FR-1.1"],
                    # No steps executed (typical for placeholders)
                    "steps": [],
                }
            ],
        }
    ]

    result = summarize_behave(behave_json)

    # Validate summary tallies
    assert result["summary"]["total"] == 1
    assert result["summary"]["passed"] == 0
    assert result["summary"]["failed"] == 0
    assert result["summary"]["skipped"] == 1

    # Validate scenario status
    assert len(result["scenarios"]) == 1
    assert result["scenarios"][0]["status"] == "skipped"

    # Validate requirements mapping picks up FR-*/NFR-* tags
    reqs = {r["id"]: r for r in result.get("requirements", [])}
    assert "FR-1.1" in reqs
    assert reqs["FR-1.1"]["status"] == "covered"
    assert "Scenario: Placeholder acceptance" in reqs["FR-1.1"]["scenarios"]
