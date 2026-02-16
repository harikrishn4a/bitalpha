"""Finnhub connector: fintech stocks + company news."""
from __future__ import annotations

import os
from datetime import datetime, timedelta

from .base import BaseSource

_BASE = "https://finnhub.io/api/v1"
_DEFAULT_SYMBOLS = ["COIN", "SQ", "MSTR", "PYPL", "HOOD", "GRAB"]


class FinnhubSource(BaseSource):
    name = "finnhub"
    _min_interval = 0.35  # 60 req/min free tier

    def __init__(self, cache, api_key: str | None = None, symbols: list[str] | None = None):
        super().__init__(cache)
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY", "")
        self.symbols = symbols or _DEFAULT_SYMBOLS

    def _params(self, extra: dict | None = None) -> dict:
        p = {"token": self.api_key}
        if extra:
            p.update(extra)
        return p

    def quote(self, symbol: str) -> dict:
        if not self.api_key:
            return {}
        try:
            return self._get(f"{_BASE}/quote", self._params({"symbol": symbol}), cache_prefix="fh")
        except Exception:
            return {}

    def company_news(self, symbol: str, days_back: int = 3) -> list[dict]:
        if not self.api_key:
            return []
        from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        to_date = datetime.utcnow().strftime("%Y-%m-%d")
        try:
            data = self._get(f"{_BASE}/company-news", self._params({
                "symbol": symbol, "from": from_date, "to": to_date,
            }), cache_prefix="fh")
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def fetch_quotes(self) -> list[dict]:
        """Fetch all watchlist quotes with % change. Returns dicts sorted by abs move."""
        quotes = []
        for sym in self.symbols:
            q = self.quote(sym)
            if q and q.get("c"):
                quotes.append({
                    "symbol": sym,
                    "price": q["c"],
                    "chg_pct": q.get("dp", 0) or 0,
                    "prev_close": q.get("pc", 0),
                    "high": q.get("h", 0),
                    "low": q.get("l", 0),
                    "raw": q,
                })
        quotes.sort(key=lambda x: abs(x["chg_pct"]), reverse=True)
        return quotes

    def fetch_signals(self) -> list[dict]:
        signals = []
        for sym in self.symbols:
            # Quote snapshot
            q = self.quote(sym)
            if q and q.get("c"):
                chg_pct = q.get("dp", 0) or 0
                signals.append({
                    "source": "finnhub",
                    "category": "fintech",
                    "headline": f"{sym} ${q['c']:.2f} ({chg_pct:+.1f}%)",
                    "body": f"{sym} current price ${q['c']:.2f}, change {chg_pct:+.1f}%. High ${q.get('h', 0):.2f}, Low ${q.get('l', 0):.2f}.",
                    "url": f"https://finance.yahoo.com/quote/{sym}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "raw_data": {"symbol": sym, "is_quote": True, **q},
                })
            # Company news
            news = self.company_news(sym, days_back=3)
            for n in news[:3]:
                signals.append({
                    "source": "finnhub",
                    "category": "fintech",
                    "headline": f"[{sym}] {n.get('headline', '')}",
                    "body": n.get("summary", ""),
                    "url": n.get("url", ""),
                    "timestamp": datetime.fromtimestamp(n.get("datetime", 0)).isoformat()
                    if n.get("datetime") else datetime.utcnow().isoformat(),
                    "raw_data": {"symbol": sym, "is_quote": False, **n},
                })
        return signals
