"""Base class for all data source connectors."""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

import requests
from requests.adapters import HTTPAdapter

from storage.cache import FileCache


class BaseSource(ABC):
    """Abstract base for API data sources with caching and rate limiting."""

    name: str = "base"
    _last_call: float = 0.0
    _min_interval: float = 0.25  # seconds between calls (4 req/s default)

    def __init__(self, cache: FileCache):
        self.cache = cache
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "bitalpha/2.0"
        # Retry on connection errors, disable keep-alive pooling to avoid stale conns
        adapter = HTTPAdapter(max_retries=2, pool_maxsize=1)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _rate_limit(self):
        elapsed = time.time() - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.time()

    def _get(self, url: str, params: dict | None = None,
             headers: dict | None = None, cache_prefix: str | None = None,
             timeout: tuple | int = (5, 15)) -> Any:
        """GET with cache-first, rate limiting, and error handling.

        timeout is (connect_timeout, read_timeout) in seconds.
        """
        prefix = cache_prefix or self.name
        cached = self.cache.get(prefix, url, params)
        if cached is not None:
            return cached
        self._rate_limit()
        if headers:
            resp = self.session.get(url, params=params, headers=headers, timeout=timeout)
        else:
            resp = self.session.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        self.cache.set(prefix, url, data, params)
        return data

    @abstractmethod
    def fetch_signals(self) -> list[dict]:
        """Fetch raw data and return a list of raw signal dicts.

        Each dict should have at minimum:
            source, category, headline, body, url, timestamp, raw_data
        """
        ...
