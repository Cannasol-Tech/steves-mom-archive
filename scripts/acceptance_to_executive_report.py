#!/usr/bin/env python3
"""
Transform Behave JSON output into the Cannasol executive-report.json format.

- Reads a Behave JSON report (formatter: -f json)
- Writes final/executive-report.json matching docs/standards/release-format.md

Defaults for this repository:
- owner: Cannasol-Tech
- repo: steves-mom-archive
- releaseTag: "local" for local runs (can be overridden via env REPORT_RELEASE_TAG)
- commit: current HEAD short SHA

Usage:
  python scripts/acceptance_to_executive_report.py --behave-json path/to/report.json --out final/executive-report.json

Env overrides:
  REPORT_OWNER, REPORT_REPO, REPORT_RELEASE_TAG, REPORT_VERSION
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def _git(cmd: List[str]) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
        return out
    except Exception:
        return ""


def detect_git_metadata() -> Dict[str, str]:
    commit = _git(["git", "rev-parse", "--short", "HEAD"]) or "unknown"
    # Derive tag if present; otherwise empty for local runs. Caller may set 'local'.
    tag = _git(["git", "describe", "--tags", "--abbrev=0"]) or ""
    return {"commit": commit, "tag": tag}


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def summarize_behave(behave_data: Any) -> Dict[str, Any]:
    # Behave JSON is typically a list of features
    features = behave_data if isinstance(behave_data, list) else []

    total = 0
    passed = 0
    failed = 0
    skipped = 0
    duration_ms = 0
    scenarios: List[Dict[str, Any]] = []
    requirements_map: Dict[str, List[str]] = {}

    def _normalize_tags(raw_tags: Any) -> List[str]:
        tags: List[str] = []
        if not raw_tags:
            return tags
        for t in raw_tags:
            if isinstance(t, dict):
                name = str(t.get("name", ""))
            else:
                name = str(t)
            name = name.lstrip("@").strip()
            if name:
                tags.append(name)
        # de-duplicate, preserve order
        return list(dict.fromkeys(tags))

    for feat in features:
        feature_name = feat.get("name", "")
        feature_tags = _normalize_tags(feat.get("tags", []) or [])
        elements = feat.get("elements", []) or []
        for el in elements:
            if el.get("type") not in ("scenario", "scenario_outline"):
                continue
            scen_name = el.get("name", "")
            # Combine scenario-level and feature-level tags for traceability
            scen_tags = _normalize_tags(el.get("tags", []) or [])
            if feature_tags:
                scen_tags = list(dict.fromkeys(scen_tags + feature_tags))  # de-duplicate, preserve order

            # Steps
            steps_out: List[Dict[str, Any]] = []
            scen_status = "unknown"
            scen_duration_ms = 0
            for st in el.get("steps", []) or []:
                res = st.get("result", {}) or {}
                status = str(res.get("status", "unknown"))
                duration = res.get("duration", 0) or 0
                # Behave duration is seconds (float); convert to ms
                try:
                    scen_duration_ms += int(float(duration) * 1000)
                except Exception:
                    pass
                steps_out.append({
                    "keyword": st.get("keyword", ""),
                    "text": st.get("name", ""),
                    "status": status,
                })
                if status in ("failed", "undefined"):
                    scen_status = "failed"
            if scen_status != "failed":
                # If any pending/undefined we marked failed already; else passed if all passed, else unknown
                if all(s.get("status") == "passed" for s in steps_out if s.get("status")):
                    scen_status = "passed"
                elif any(s.get("status") == "skipped" for s in steps_out):
                    scen_status = "skipped"
                else:
                    scen_status = "unknown"

            # Tally
            total += 1
            if scen_status == "passed":
                passed += 1
            elif scen_status == "failed":
                failed += 1
            elif scen_status == "skipped":
                skipped += 1
            duration_ms += scen_duration_ms

            # Requirements mapping from tags like PRD-123
            prd_tags = [t for t in scen_tags if t.upper().startswith("PRD-")]
            for prd in prd_tags:
                requirements_map.setdefault(prd.upper(), []).append(scen_name)

            scenarios.append({
                "feature": feature_name,
                "name": scen_name,
                "status": scen_status,
                "durationMs": scen_duration_ms,
                "steps": steps_out,
                "tags": scen_tags,
            })

    requirements = [
        {"id": rid, "status": "covered" if names else "unknown", "scenarios": names}
        for rid, names in sorted(requirements_map.items())
    ]

    return {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "durationMs": duration_ms,
        },
        "scenarios": scenarios,
        "requirements": requirements,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--behave-json", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    behave_path = Path(args.behave_json)
    out_path = Path(args.out)

    if not behave_path.exists():
        # Still write an empty but valid report to satisfy the standard
        behave_data: Any = []
    else:
        with behave_path.open("r", encoding="utf-8") as f:
            try:
                behave_data = json.load(f)
            except Exception:
                behave_data = []

    repo_owner = os.environ.get("REPORT_OWNER", "Cannasol-Tech")
    repo_name = os.environ.get("REPORT_REPO", "steves-mom-archive")

    git_meta = detect_git_metadata()
    commit = git_meta["commit"] or os.environ.get("REPORT_COMMIT", "unknown")

    # releaseTag: prefer env override; else if local run set to "local"; else git tag if present
    release_tag = os.environ.get("REPORT_RELEASE_TAG", "")
    if not release_tag:
        release_tag = "local" if os.environ.get("CI", "false").lower() != "true" else (git_meta["tag"] or "")

    base = summarize_behave(behave_data)

    report: Dict[str, Any] = {
        "version": os.environ.get("REPORT_VERSION", "1.0.0"),
        "owner": repo_owner,
        "repo": repo_name,
        "releaseTag": release_tag,
        "commit": commit,
        "createdAt": iso_now(),
        "summary": base["summary"],
        "scenarios": base["scenarios"],
        "requirements": base["requirements"],
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Wrote executive report: {out_path}")


if __name__ == "__main__":
    main()
