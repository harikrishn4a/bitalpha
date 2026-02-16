"""CoinGecko + Alternative.me Fear & Greed connector."""
from __future__ import annotations

import os
from datetime import datetime

from .base import BaseSource

_CG_BASE = "https://api.coingecko.com/api/v3"
_FNG_BASE = "https://api.alternative.me/fng"


class CoinGeckoSource(BaseSource):
    name = "coingecko"
    _min_interval = 0.5  # free tier ~10-30 req/min

    def __init__(self, cache, api_key: str | None = None):
        super().__init__(cache)
        self.api_key = api_key or os.getenv("COINGECKO_API_KEY", "")
        if self.api_key:
            # CG- prefix = demo key; otherwise assume pro key
            if self.api_key.startswith("CG-"):
                self.session.headers["x-cg-demo-api-key"] = self.api_key
            else:
                self.session.headers["x-cg-pro-api-key"] = self.api_key

    # ── Price endpoints ──

    def simple_price(self, vs: str = "usd,sgd") -> dict:
        return self._get(f"{_CG_BASE}/simple/price", {"ids": "bitcoin", "vs_currencies": vs}, cache_prefix="cg")

    def coin_detail(self) -> dict:
        return self._get(f"{_CG_BASE}/coins/bitcoin", {
            "localization": "false", "tickers": "false",
            "community_data": "false", "developer_data": "false",
        }, cache_prefix="cg")

    def market_chart(self, days: int = 90, vs: str = "usd") -> dict:
        return self._get(f"{_CG_BASE}/coins/bitcoin/market_chart", {
            "vs_currency": vs, "days": str(days),
        }, cache_prefix="cg")

    def ohlc(self, days: int = 30, vs: str = "usd") -> list:
        """OHLC candles. Returns [[ts, open, high, low, close], ...]."""
        return self._get(f"{_CG_BASE}/coins/bitcoin/ohlc", {
            "vs_currency": vs, "days": str(days),
        }, cache_prefix="cg")

    # ── Global market data (dominance, volume) ──

    def global_data(self) -> dict:
        """Get global crypto market data: dominance, volume, market cap."""
        try:
            data = self._get(f"{_CG_BASE}/global", cache_prefix="cg")
            return data.get("data", {})
        except Exception:
            return {}

    # ── Fear & Greed ──

    def fear_greed_latest(self) -> dict:
        return self._get(f"{_FNG_BASE}/", {"limit": "1"}, cache_prefix="fng")

    def fear_greed_history(self, days: int = 30) -> dict:
        return self._get(f"{_FNG_BASE}/", {"limit": str(days)}, cache_prefix="fng")

    # ── Signal interface ──

    def fetch_signals(self) -> list[dict]:
        signals = []
        now = datetime.utcnow().isoformat()
        # BTC price snapshot
        try:
            detail = self.coin_detail()
            md = detail.get("market_data", {})
            price = md.get("current_price", {}).get("usd")
            chg_24h = md.get("price_change_percentage_24h")
            chg_7d = md.get("price_change_percentage_7d")
            ath = md.get("ath", {}).get("usd")
            signals.append({
                "source": "coingecko",
                "category": "crypto_catalyst",
                "headline": f"BTC ${price:,.0f} | 24h {chg_24h:+.1f}% | 7d {chg_7d:+.1f}%",
                "body": f"Current BTC price ${price:,.0f}. 24h change {chg_24h:+.1f}%, 7d change {chg_7d:+.1f}%. ATH ${ath:,.0f}.",
                "url": "https://www.coingecko.com/en/coins/bitcoin",
                "timestamp": now,
                "raw_data": {
                    "price_usd": price, "chg_24h": chg_24h, "chg_7d": chg_7d,
                    "ath_usd": ath, "market_data": md,
                },
            })
        except Exception:
            pass
        # Fear & Greed
        try:
            fng = self.fear_greed_latest()
            data = fng.get("data", [{}])
            if data:
                val = data[0].get("value", "N/A")
                cls = data[0].get("value_classification", "N/A")
                signals.append({
                    "source": "coingecko",
                    "category": "crypto_catalyst",
                    "headline": f"Fear & Greed: {val} ({cls})",
                    "body": f"Crypto Fear & Greed Index at {val} — {cls}.",
                    "url": "https://alternative.me/crypto/fear-and-greed-index/",
                    "timestamp": now,
                    "raw_data": {"fng_value": val, "fng_class": cls},
                })
        except Exception:
            pass
        return signals
