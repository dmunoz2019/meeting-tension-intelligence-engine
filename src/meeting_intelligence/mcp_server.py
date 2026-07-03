from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .engine import MeetingIntelligenceEngine


def create_server(data_dir: str | Path | None = None):
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("Install the MCP extra: pip install -e '.[mcp]'") from exc

    root = Path(data_dir or os.getenv("MEETING_INTELLIGENCE_DATA_DIR", "/data/private")).resolve()
    root.mkdir(parents=True, exist_ok=True)
    transcript_dir = root / "transcripts"
    result_dir = root / "results"
    transcript_dir.mkdir(exist_ok=True)
    result_dir.mkdir(exist_ok=True)
    max_quote_chars = int(os.getenv("MEETING_INTELLIGENCE_MAX_QUOTE_CHARS", "240"))
    engine = MeetingIntelligenceEngine()
    mcp = FastMCP("Meeting Tension Intelligence")

    def safe_path(directory: Path, filename: str) -> Path:
        candidate = (directory / filename).resolve()
        if directory not in candidate.parents:
            raise ValueError("path escapes configured data directory")
        return candidate

    @mcp.tool()
    def meetings_list() -> dict[str, Any]:
        """List private transcript files available for analysis."""
        return {
            "meetings": [
                {"name": path.name, "size": path.stat().st_size}
                for path in sorted(transcript_dir.glob("*.md"))
            ]
        }

    @mcp.tool()
    def meeting_analyze(filename: str) -> dict[str, Any]:
        """Analyze a transcript and save structured private results."""
        source = safe_path(transcript_dir, filename)
        text = source.read_text(encoding="utf-8")
        payload = engine.analyze(text)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        output = safe_path(result_dir, f"{source.stem}.analysis.json")
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "source": source.name,
            "source_sha256": digest,
            "summary": payload["summary"],
            "top_findings": [
                {
                    **{key: value for key, value in finding.items() if key != "context"},
                    "sentence": finding["sentence"][:max_quote_chars],
                }
                for finding in payload["findings"][:20]
            ],
            "saved_result": output.name,
        }

    @mcp.tool()
    def meeting_get_batch(filename: str, cursor: int = 0, limit: int = 25) -> dict[str, Any]:
        """Return a bounded batch of previously analyzed findings."""
        source = safe_path(result_dir, filename)
        payload = json.loads(source.read_text(encoding="utf-8"))
        findings = payload.get("findings", [])
        batch = findings[cursor:cursor + max(1, min(limit, 100))]
        return {
            "cursor": cursor,
            "next_cursor": cursor + len(batch),
            "has_more": cursor + len(batch) < len(findings),
            "findings": [
                {**item, "sentence": item["sentence"][:max_quote_chars]}
                for item in batch
            ],
        }

    return mcp


def run_server(data_dir: str | Path | None = None) -> None:
    create_server(data_dir).run(transport="streamable-http")
