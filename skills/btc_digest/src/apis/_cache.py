"""Simple JSON file cache with TTL."""
import hashlib
import json
import time
from pathlib import Path

from ..config import CACHE_DIR, CACHE_TTL_SEC


def _cache_key(url: str, params: dict) -> str:
    s = url + json.dumps(params or {}, sort_keys=True)
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def get_cached(key_prefix: str, url: str, params: dict | None = None) -> dict | list | None:
    """Return cached JSON if fresh, else None."""
    key = f"{key_prefix}_{_cache_key(url, params)}.json"
    path = CACHE_DIR / key
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > CACHE_TTL_SEC:
        return None
    with open(path) as f:
        return json.load(f)


def set_cached(key_prefix: str, url: str, data: dict | list, params: dict | None = None):
    """Write JSON to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = f"{key_prefix}_{_cache_key(url, params)}.json"
    path = CACHE_DIR / key
    with open(path, "w") as f:
        json.dump(data, f)
