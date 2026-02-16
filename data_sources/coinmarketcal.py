"""CoinMarketCal connector: crypto catalyst events."""
from __future__ import annotations

import os
from datetime import datetime

from .base import BaseSource

_BASE = "https://developers.coinmarketcal.com/v1"


class CoinMarketCalSource(BaseSource):
    name = "coinmarketcal"
    _min_interval = 1.0  # conservative

    def __init__(self, cache, api_key: str | None = None):
        super().__init__(cache)
        self.api_key = api_key or os.getenv("COINMARKETCAL_API_KEY", "")

    def _headers(self) -> dict:
        return {"x-api-key": self.api_key, "Accept": "application/json"}

    def fetch_events(self, coins: str = "bitcoin", max_results: int = 20) -> list[dict]:
        """Fetch upcoming crypto events from CoinMarketCal."""
        if not self.api_key:
            return []
        try:
            data = self._get(
                f"{_BASE}/events",
                params={"coins": coins, "max": str(max_results), "sortBy": "date_event"},
                headers=self._headers(),
                cache_prefix="cmc",
            )
            return data.get("body", []) if isinstance(data, dict) else data
        except Exception:
            return []

    def fetch_signals(self) -> list[dict]:
        events = self.fetch_events()
        signals = []
        for ev in events:
            title = ev.get("title", {})
            if isinstance(title, dict):
                title = title.get("en", str(title))
            coins = [c.get("symbol", "") for c in ev.get("coins", [])]
            date_event = ev.get("date_event", datetime.utcnow().isoformat())
            source_url = ev.get("source", "")
            proof_url = ev.get("proof", source_url)
            signals.append({
                "source": "coinmarketcal",
                "category": "crypto_catalyst",
                "headline": f"[{', '.join(coins)}] {title}",
                "body": ev.get("description", title),
                "url": proof_url or f"https://coinmarketcal.com/en/event/{ev.get('id', '')}",
                "timestamp": date_event,
                "raw_data": ev,
            })
        return signals
