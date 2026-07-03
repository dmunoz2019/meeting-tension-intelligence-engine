from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import MeetingIntelligenceEngine
from .export import export_findings_csv
from .mcp_server import run_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="meeting-intelligence")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze a transcript")
    analyze.add_argument("transcript", type=Path)
    analyze.add_argument("--output-dir", type=Path, default=Path("output"))
    analyze.add_argument("--minimum-tension", type=float, default=16.0)

    discover = subparsers.add_parser("discover", help="Discover adaptive regex patterns")
    discover.add_argument("transcript", type=Path)
    discover.add_argument("--output", type=Path, required=True)
    discover.add_argument("--limit", type=int, default=80)

    serve = subparsers.add_parser("serve-mcp", help="Run the MCP server")
    serve.add_argument("--data-dir", type=Path, default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "serve-mcp":
        run_server(args.data_dir)
        return 0

    engine = MeetingIntelligenceEngine(
        minimum_tension=getattr(args, "minimum_tension", 16.0)
    )
    text = args.transcript.read_text(encoding="utf-8")

    if args.command == "discover":
        patterns = [pattern.to_dict() for pattern in engine.discover(text, limit=args.limit)]
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(patterns, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"patterns": len(patterns), "output": str(args.output)}, indent=2))
        return 0

    payload = engine.analyze(text)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "analysis.json"
    csv_path = args.output_dir / "findings.csv"
    engine.save_json(payload, json_path)
    export_findings_csv(payload, csv_path)
    print(
        json.dumps(
            {"summary": payload["summary"], "json": str(json_path), "csv": str(csv_path)},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
