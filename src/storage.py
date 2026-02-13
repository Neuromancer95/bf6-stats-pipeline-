"""
Storage layer: write pipeline results to JSON, CSV, or SQLite.
"""

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Keys to include in flattened summary row for CSV / SQLite
SUMMARY_KEYS = [
    "userName",
    "id",
    "userId",
    "kills",
    "deaths",
    "wins",
    "loses",
    "winPercent",
    "killDeath",
    "killsPerMinute",
    "damagePerMinute",
    "accuracy",
    "headshots",
    "timePlayed",
    "secondsPlayed",
    "matchesPlayed",
    "revives",
    "heals",
    "resupplies",
    "repairs",
]

# SQLite table columns: run_id and fetched_at first, then SUMMARY_KEYS
SQLITE_COLUMNS = ["run_id", "fetched_at"] + SUMMARY_KEYS


def _stats_filename(run_id: str | None, extension: str) -> str:
    """Return stats filename: stats_{run_id}.{ext} or stats_{timestamp}.{ext}."""
    if run_id:
        return f"stats_{run_id}.{extension}"
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"stats_{ts}.{extension}"


def _ensure_output_dir(output_dir: Path) -> Path:
    """Create output directory if needed; return Path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def flatten_summary(stats: dict) -> dict:
    """Extract a flat summary dict from full stats JSON for one player."""
    out = {
        "fetched_at": datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
    }
    for key in SUMMARY_KEYS:
        if key in stats:
            out[key] = stats[key]
    return out


def _all_summary_keys(summaries: list[dict]) -> list[str]:
    """Collect all keys from summaries (for CSV header), preserving order."""
    keys = list(summaries[0].keys())
    for s in summaries[1:]:
        for k in s:
            if k not in keys:
                keys.append(k)
    return keys


def save_json(
    results: list[dict], output_dir: Path, run_id: str | None = None
) -> Path:
    """
    Write one JSON file per run.

    Filename: stats_YYYYMMDD_HHMMSS.json or stats_{run_id}.json.
    """
    out_dir = _ensure_output_dir(output_dir)
    path = out_dir / _stats_filename(run_id, "json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    return path


def save_csv(
    results: list[dict], output_dir: Path, run_id: str | None = None
) -> Path:
    """
    Write one CSV file: one row per player (flattened summary), with timestamp.
    """
    if not results:
        raise ValueError("No results to write to CSV")
    summaries = [flatten_summary(r) for r in results]
    out_dir = _ensure_output_dir(output_dir)
    path = out_dir / _stats_filename(run_id, "csv")
    fieldnames = _all_summary_keys(summaries)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summaries)
    return path


def save_sqlite(
    results: list[dict],
    output_dir: Path,
    db_name: str = "bf6_stats.db",
    run_id: str | None = None,
) -> Path:
    """
    Append flattened summary rows to SQLite.

    Table: stats (run_id, fetched_at, ...SUMMARY_KEYS).
    """
    if not results:
        return Path(output_dir) / db_name
    out_dir = _ensure_output_dir(output_dir)
    db_path = out_dir / db_name
    now = datetime.now(timezone.utc)
    fetched_at = now.isoformat().replace("+00:00", "Z")
    rid = run_id or now.strftime("%Y%m%d_%H%M%S")

    # Schema: all columns as TEXT for simplicity (SQLite is flexible)
    col_defs = ", ".join(f"{c} TEXT" for c in SQLITE_COLUMNS)
    placeholders = ", ".join(f":{c}" for c in SQLITE_COLUMNS)
    insert_sql = (
        f"INSERT INTO stats ({', '.join(SQLITE_COLUMNS)}) "
        f"VALUES ({placeholders})"
    )

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            f"CREATE TABLE IF NOT EXISTS stats ({col_defs})"
        )
        for stat in results:
            summary = flatten_summary(stat)
            summary["run_id"] = rid
            summary["fetched_at"] = fetched_at
            row = {c: summary.get(c) for c in SQLITE_COLUMNS}
            cur.execute(insert_sql, row)
        conn.commit()
    finally:
        conn.close()
    return db_path
