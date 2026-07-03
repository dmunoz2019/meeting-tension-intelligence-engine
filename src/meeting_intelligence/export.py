from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def export_findings_csv(payload: dict[str, Any], path: str | Path) -> None:
    findings = payload.get("findings", [])
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "unit_id",
        "start",
        "end",
        "sentence",
        "act",
        "sentiment",
        "dissatisfaction_score",
        "project_risk_score",
        "tension_score",
        "tension_level",
        "certainty",
        "review_required",
        "direct_concern",
        "reported_concern",
        "hypothetical",
        "hedged",
        "adaptive_pattern_ids",
        "context",
    ]
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for finding in findings:
            row = {field: finding.get(field, "") for field in fields}
            row["adaptive_pattern_ids"] = " | ".join(finding.get("adaptive_pattern_ids", []))
            writer.writerow(row)
