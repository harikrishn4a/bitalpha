"""CoinGlass connector: BTC ETF flows (requires paid API key)."""
from __future__ import annotations

import os
from datetime import datetime

from .base import BaseSource

_BASE = "https://open-api-v3.coinglass.com/api"


class CoinGlassSource(BaseSource):
    name = "coinglass"
    _min_interval = 1.0

    def __init__(self, cache, api_key: str | None = None):
        super().__init__(cache)
        self.api_key = api_key or os.getenv("COINGLASS_API_KEY", "")

    def _headers(self) -> dict:
        return {"coinglassSecret": self.api_key, "Accept": "application/json"}

    def etf_flows(self) -> dict | None:
        """Fetch BTC ETF net flow data. Returns None if no key."""
        if not self.api_key:
            return None
        try:
            data = self._get(
                f"{_BASE}/etf/btc-etf-flow-total",
                headers=self._headers(),
                cache_prefix="cg_etf",
            )
            return data if isinstance(data, dict) else None
        except Exception:
            return None

    def fetch_signals(self) -> list[dict]:
        flows = self.etf_flows()
        if not flows:
            return []
        signals = []
        flow_data = flows.get("data", {})
        if isinstance(flow_data, dict):
            net_flow = flow_data.get("netFlow")
            if net_flow is not None:
                direction = "inflow" if net_flow > 0 else "outflow"
                signals.append({
                    "source": "coinglass",
                    "category": "crypto_catalyst",
                    "headline": f"BTC ETF net {direction}: ${abs(net_flow):,.0f}M",
                    "body": f"Total BTC ETF net flow: ${net_flow:+,.0f}M. {'Institutional buying' if net_flow > 0 else 'Institutional selling'} pressure.",
                    "url": "https://www.coinglass.com/bitcoin-etf",
                    "timestamp": datetime.utcnow().isoformat(),
                    "raw_data": flow_data,
                })
        return signals
