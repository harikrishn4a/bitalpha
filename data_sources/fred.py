"""FRED API connector: macro series observations + releases calendar."""
from __future__ import annotations

import os
from datetime import datetime, timedelta

from .base import BaseSource

_BASE = "https://api.stlouisfed.org"
_DEFAULT_SERIES = ["DGS10", "DTWEXBGS", "T10Y2Y", "ICSA", "CPIAUCSL", "FEDFUNDS", "DGS2"]


class FredSource(BaseSource):
    name = "fred"
    _min_interval = 0.5  # FRED is generous but be polite

    def __init__(self, cache, api_key: str | None = None, series: list[str] | None = None):
        super().__init__(cache)
        self.api_key = api_key or os.getenv("FRED_API_KEY", "")
        self.series = series or _DEFAULT_SERIES
        # FRED silently drops requests with custom User-Agent headers
        self.session.headers.pop("User-Agent", None)

    def _fred_get(self, endpoint: str, params: dict | None = None):
        if not self.api_key:
            return None
        p = {"api_key": self.api_key, "file_type": "json", **(params or {})}
        return self._get(f"{_BASE}{endpoint}", p, cache_prefix="fred")

    # ── Series observations ──

    def fetch_series(self, series_id: str, limit: int = 5) -> list[dict]:
        """Fetch recent observations for a FRED series."""
        data = self._fred_get("/fred/series/observations", {
            "series_id": series_id,
            "sort_order": "desc",
            "limit": str(limit),
        })
        if not data:
            return []
        return data.get("observations", [])

    def fetch_all_series(self) -> dict[str, list[dict]]:
        """Fetch all configured series. Returns {series_id: [observations]}."""
        out = {}
        for sid in self.series:
            obs = self.fetch_series(sid)
            if obs:
                out[sid] = obs
        return out

    # ── Releases calendar ──

    def fetch_releases(self, days_ahead: int = 14) -> list[dict]:
        """Fetch upcoming FRED release dates."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        end = (datetime.utcnow() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        data = self._fred_get("/fred/releases/dates", {
            "include_release_dates_with_no_data": "true",
            "sort_order": "asc",
            "realtime_start": today,
            "realtime_end": end,
        })
        if not data:
            return []
        return data.get("release_dates", [])

    # ── Signal interface ──

    def fetch_signals(self) -> list[dict]:
        signals = []
        # Upcoming releases as signals
        releases = self.fetch_releases()
        for r in releases:
            signals.append({
                "source": "fred",
                "category": "macro",
                "headline": f"{r.get('release_name', 'FRED release')} — {r.get('date', '')}",
                "body": f"Upcoming FRED release: {r.get('release_name', '')}",
                "url": f"https://fred.stlouisfed.org/releases/{r.get('release_id', '')}",
                "timestamp": r.get("date", datetime.utcnow().isoformat()),
                "raw_data": r,
            })
        # Current series snapshots (for regime / macro dashboard, not signals per se)
        all_series = self.fetch_all_series()
        for sid, obs in all_series.items():
            if not obs:
                continue
            latest = obs[0]
            val = latest.get("value", ".")
            if val == ".":
                continue
            signals.append({
                "source": "fred",
                "category": "macro",
                "headline": f"FRED {sid}: {val}",
                "body": f"Latest {sid} observation: {val} as of {latest.get('date', '')}",
                "url": f"https://fred.stlouisfed.org/series/{sid}",
                "timestamp": latest.get("date", datetime.utcnow().isoformat()),
                "raw_data": {"series_id": sid, "observations": obs},
            })
        return signals
