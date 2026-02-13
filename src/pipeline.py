"""
Pipeline: load config -> resolve players -> fetch stats (single or batch).

Returns list of full stat dicts.
"""

import json
from pathlib import Path

from src.api import BF6APIClient, BF6APIError

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

BATCH_SIZE = 128


def load_config(path: str | Path) -> list[dict]:
    """
    Load player list from config file. Expects format:
    - YAML: { players: [ { name: "...", platform: "pc" }, ... ] }
    - JSON: { "players": [ { "name": "...", "platform": "pc" }, ... ] }
    Returns list of { name, platform } dicts.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        if not HAS_YAML:
            raise ImportError(
                "PyYAML required for YAML config. pip install pyyaml"
            )
        data = yaml.safe_load(text)
    elif suffix == ".json":
        data = json.loads(text)
    else:
        raise ValueError(f"Unsupported config format: {suffix}. Use .yaml or .json")
    players = data.get("players", data) if isinstance(data, dict) else data
    if not isinstance(players, list):
        raise ValueError("Config must contain a 'players' list")
    out = []
    for p in players:
        if isinstance(p, dict) and "name" in p:
            out.append({
                "name": str(p["name"]),
                "platform": str(p.get("platform", "pc")),
            })
        else:
            raise ValueError(f"Invalid player entry: {p}")
    return out


def run_pipeline(
    players: list[dict],
    *,
    use_batch: bool = True,
    rate_limit_sec: float = 1.0,
) -> list[dict]:
    """
    Resolve player IDs, fetch stats (single or batch), return list of stat dicts.

    players: list of {"name": "...", "platform": "pc"} dicts.
    use_batch: if True and len(players) > 1, use POST /bf6/multiple/ (up to 128).
    """
    client = BF6APIClient(rate_limit_sec=rate_limit_sec)
    results: list[dict] = []
    if use_batch and len(players) > 1:
        # Resolve all IDs first
        ids_by_platform: dict[str, list[str]] = {}
        for p in players:
            platform = p["platform"]
            try:
                info = client.get_player_id(p["name"], platform)
                pid = str(
                    info.get("id", info) if isinstance(info, dict) else info
                )
                ids_by_platform.setdefault(platform, []).append(pid)
            except BF6APIError:
                continue
        for platform, id_list in ids_by_platform.items():
            for i in range(0, len(id_list), BATCH_SIZE):
                chunk = id_list[i : i + BATCH_SIZE]
                batch = client.get_stats_batch(chunk, platform=platform)
                results.extend(batch)
    else:
        for p in players:
            try:
                stats = client.get_stats(name=p["name"], platform=p["platform"])
                results.append(stats)
            except BF6APIError:
                continue
    return results
