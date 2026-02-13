#!/usr/bin/env python3
"""
BF6 Player Stats Pipeline — CLI.

Usage:
  python main.py --config config.yaml --output-dir output --format json
  python main.py --players "name1,pc;name2,psn" --output-dir output --format all
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.pipeline import load_config, run_pipeline
from src.storage import save_csv, save_json, save_sqlite


def parse_players_arg(s: str) -> list[dict]:
    """Parse --players "name1,platform1;name2,platform2" into list of dicts."""
    out = []
    for part in s.split(";"):
        part = part.strip()
        if not part:
            continue
        if "," in part:
            name, platform = part.split(",", 1)
            out.append({"name": name.strip(), "platform": platform.strip() or "pc"})
        else:
            out.append({"name": part.strip(), "platform": "pc"})
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pull BF6 player stats from GameTools.Network and save to JSON, CSV, or SQLite."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Config file (YAML or JSON) with 'players' list (default: config.yaml)",
    )
    parser.add_argument(
        "--players",
        type=str,
        default=None,
        help='Override config: "name1,platform1;name2,platform2" (platform defaults to pc)',
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for output files (default: output)",
    )
    parser.add_argument(
        "--format",
        choices=("json", "csv", "sqlite", "all"),
        default="json",
        help="Output format: json, csv, sqlite, or all (default: json)",
    )
    parser.add_argument(
        "--no-batch",
        action="store_true",
        help="Fetch stats one-by-one instead of using batch API",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="Seconds between API requests (default: 1.0)",
    )
    args = parser.parse_args()

    if args.players:
        players = parse_players_arg(args.players)
    else:
        try:
            players = load_config(args.config)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except (ValueError, ImportError) as e:
            print(f"Config error: {e}", file=sys.stderr)
            return 1

    if not players:
        print(
            "No players to fetch. Add entries in config or use --players.",
            file=sys.stderr,
        )
        return 1

    run_id = None  # storage will use timestamp if None
    results = run_pipeline(
        players,
        use_batch=not args.no_batch,
        rate_limit_sec=args.rate_limit,
    )

    if not results:
        print(
            "No stats retrieved. Check player names and platforms.",
            file=sys.stderr,
        )
        return 1

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    writers = (
        ("json", save_json, "JSON"),
        ("csv", save_csv, "CSV"),
        ("sqlite", save_sqlite, "SQLite"),
    )
    for fmt, save_fn, label in writers:
        if args.format in (fmt, "all"):
            path = save_fn(results, out_dir, run_id=run_id)
            print(f"Wrote {label}: {path}")

    print(f"Fetched {len(results)} player(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
