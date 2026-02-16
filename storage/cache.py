"""File-based JSON cache with TTL. Adapted from original _cache.py."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

_DEFAULT_TTL = 300  # seconds


class FileCache:
    """Simple file-based cache. Each entry is a JSON file keyed by hash."""

    def __init__(self, cache_dir: str | Path, ttl: int = _DEFAULT_TTL):
        self.dir = Path(cache_dir).expanduser().resolve()
        self.dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl

    def _key(self, prefix: str, url: str, params: dict | None = None) -> str:
        raw = url + (json.dumps(params, sort_keys=True) if params else "")
        h = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"{prefix}_{h}"

    def _path(self, key: str) -> Path:
        return self.dir / f"{key}.json"

    def get(self, prefix: str, url: str, params: dict | None = None):
        """Return cached data if fresh, else None."""
        p = self._path(self._key(prefix, url, params))
        if not p.exists():
            return None
        try:
            raw = json.loads(p.read_text())
            if time.time() - raw.get("_ts", 0) > self.ttl:
                return None
            return raw.get("data")
        except (json.JSONDecodeError, KeyError):
            return None

    def set(self, prefix: str, url: str, data, params: dict | None = None):
        """Write data to cache."""
        p = self._path(self._key(prefix, url, params))
        p.write_text(json.dumps({"_ts": time.time(), "data": data}))

    def clear(self):
        """Remove all cached files."""
        for f in self.dir.glob("*.json"):
            f.unlink(missing_ok=True)
