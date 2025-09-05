#!/usr/bin/env python3
"""
Validate final/executive-report.json against the required release format
from docs/standards/release-format.md.

This is a pragmatic validator (no external jsonschema dep) that checks:
- top-level required fields exist and are of correct types
- summary fields and types
- scenarios array with required fields and step structure
- requirements array with required fields

Exit codes:
- 0: valid
- 1: invalid (prints reasons)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def fail(msg: str) -> None:
    print(f"[report-validation] ERROR: {msg}")


def require_keys(obj: Dict[str, Any], keys: List[str], ctx: str) -> List[str]:
    errs: List[str] = []
    for k in keys:
        if k not in obj:
            errs.append(f"Missing key '{k}' in {ctx}")
    return errs


def validate(report: Dict[str, Any]) -> List[str]:
    errs: List[str] = []

    # Top-level
    required_top = [
        "version",
        "owner",
        "repo",
        "releaseTag",
        "commit",
        "createdAt",
        "summary",
        "scenarios",
        "requirements",
    ]
    errs += require_keys(report, required_top, "report")

    # Type checks
    if not isinstance(report.get("version"), str):
        errs.append("'version' must be string")
    if not isinstance(report.get("owner"), str):
        errs.append("'owner' must be string")
    if not isinstance(report.get("repo"), str):
        errs.append("'repo' must be string")
    if not isinstance(report.get("releaseTag"), str):
        errs.append("'releaseTag' must be string")
    if not isinstance(report.get("commit"), str):
        errs.append("'commit' must be string")
    if not isinstance(report.get("createdAt"), str):
        errs.append("'createdAt' must be ISO8601 string")

    # Summary
    summary = report.get("summary", {})
    if not isinstance(summary, dict):
        errs.append("'summary' must be object")
    else:
        errs += require_keys(summary, ["total", "passed", "failed", "skipped", "durationMs"], "summary")
        for k in ["total", "passed", "failed", "skipped", "durationMs"]:
            if not isinstance(summary.get(k), int):
                errs.append(f"'summary.{k}' must be integer")

    # Scenarios
    scenarios = report.get("scenarios")
    if not isinstance(scenarios, list):
        errs.append("'scenarios' must be array")
    else:
        for i, scen in enumerate(scenarios):
            if not isinstance(scen, dict):
                errs.append(f"scenario[{i}] must be object")
                continue
            errs += require_keys(scen, ["feature", "name", "status", "durationMs", "steps", "tags"], f"scenario[{i}]")
            if not isinstance(scen.get("feature"), str):
                errs.append(f"scenario[{i}].feature must be string")
            if not isinstance(scen.get("name"), str):
                errs.append(f"scenario[{i}].name must be string")
            if scen.get("status") not in ("passed", "failed", "skipped", "unknown"):
                errs.append(f"scenario[{i}].status must be one of passed|failed|skipped|unknown")
            if not isinstance(scen.get("durationMs"), int):
                errs.append(f"scenario[{i}].durationMs must be integer")
            if not isinstance(scen.get("tags"), list):
                errs.append(f"scenario[{i}].tags must be array")
            steps = scen.get("steps")
            if not isinstance(steps, list):
                errs.append(f"scenario[{i}].steps must be array")
            else:
                for j, st in enumerate(steps):
                    if not isinstance(st, dict):
                        errs.append(f"scenario[{i}].steps[{j}] must be object")
                        continue
                    errs += require_keys(st, ["keyword", "text", "status"], f"scenario[{i}].steps[{j}]")
                    if not isinstance(st.get("keyword"), str):
                        errs.append(f"scenario[{i}].steps[{j}].keyword must be string")
                    if not isinstance(st.get("text"), str):
                        errs.append(f"scenario[{i}].steps[{j}].text must be string")
                    if st.get("status") not in ("passed", "failed", "skipped", "undefined", "unknown"):
                        errs.append(f"scenario[{i}].steps[{j}].status invalid")

    # Requirements
    reqs = report.get("requirements")
    if not isinstance(reqs, list):
        errs.append("'requirements' must be array")
    else:
        for i, rq in enumerate(reqs):
            if not isinstance(rq, dict):
                errs.append(f"requirements[{i}] must be object")
                continue
            errs += require_keys(rq, ["id", "status", "scenarios"], f"requirements[{i}]")
            if not isinstance(rq.get("id"), str):
                errs.append(f"requirements[{i}].id must be string")
            if rq.get("status") not in ("covered", "unknown"):
                errs.append(f"requirements[{i}].status must be 'covered' or 'unknown'")
            if not isinstance(rq.get("scenarios"), list):
                errs.append(f"requirements[{i}].scenarios must be array")

    return errs


def main() -> int:
    path = Path("final/executive-report.json")
    if not path.exists():
        fail("final/executive-report.json not found")
        return 1
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        fail(f"Failed to parse JSON: {e}")
        return 1

    errs = validate(data)
    if errs:
        for e in errs:
            fail(e)
        print("[report-validation] Result: INVALID")
        return 1

    print("[report-validation] Result: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
