#!/usr/bin/env python3
"""Clear cache and signal history so the next run fetches fresh data (for testing).

Run this before testing weekly/daily/hourly if you want to avoid deduplication
and cached API responses. Example:

    ./bin/clear_test_data.sh
    # or
    python scripts/clear_test_data.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env")

import yaml
from storage.cache import FileCache
from storage.db import SignalDB


def main():
    cfg_path = _ROOT / "config.yaml"
    cfg = {}
    if cfg_path.exists():
        with open(cfg_path) as f:
            cfg = yaml.safe_load(f) or {}

    cache_dir = os.getenv("CACHE_DIR", str(_ROOT / ".cache"))
    db_path = os.getenv("DB_PATH", str(_ROOT / "storage" / "signals.db"))
    ttl = cfg.get("cache", {}).get("ttl_seconds", 300)

    cache = FileCache(cache_dir, ttl=ttl)
    db = SignalDB(db_path)

    # Clear file cache (API responses) so next run re-fetches
    count = len(list(Path(cache.dir).glob("*.json")))
    cache.clear()
    print(f"Cleared {count} cached API response(s) from {cache.dir}")

    # Clear signals table so dedupe doesn't filter everything on next run
    db.clear_signals()
    print(f"Cleared signal history in {db.path}")

    db.close()
    print("Done. Next weekly/daily/hourly run will use fresh data.")


if __name__ == "__main__":
    main()
    sys.exit(0)
