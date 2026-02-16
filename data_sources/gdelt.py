"""GDELT DOC API connector for crypto/fintech news discovery."""
from __future__ import annotations

from datetime import datetime, timedelta

from .base import BaseSource

_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"

_DEFAULT_KEYWORDS = ["bitcoin", "crypto", "fintech", "stablecoin", "blockchain"]


def _matches_keywords(text: str, keywords: list[str]) -> bool:
    """True if text (case-insensitive) contains at least one keyword."""
    if not keywords:
        return True
    lower = text.lower()
    return any(kw.lower() in lower for kw in keywords)


class GDELTSource(BaseSource):
    name = "gdelt"
    _min_interval = 2.0  # GDELT can be slow; be respectful

    def __init__(self, cache, keywords: list[str] | None = None, filter_keywords: list[str] | None = None):
        super().__init__(cache)
        self.keywords = keywords or _DEFAULT_KEYWORDS
        self.filter_keywords = filter_keywords  # client-side: only keep articles matching these

    def fetch_articles(self, days_back: int = 2, max_records: int = 20) -> list[dict]:
        q = " OR ".join(self.keywords)
        start = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y%m%d%H%M%S")
        end = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        try:
            data = self._get(_BASE, {
                "query": q,
                "mode": "ArtList",
                "maxrecords": str(max_records),
                "format": "json",
                "startdatetime": start,
                "enddatetime": end,
                "sort": "DateDesc",
            }, cache_prefix="gdelt")
            return data.get("articles", []) if isinstance(data, dict) else []
        except Exception:
            return []

    def fetch_signals(self) -> list[dict]:
        articles = self.fetch_articles()
        signals = []
        for a in articles:
            title = a.get("title", "")
            body = a.get("seendate", "") or a.get("body", "") or ""
            if self.filter_keywords and not _matches_keywords(title + " " + body, self.filter_keywords):
                continue
            signals.append({
                "source": "gdelt",
                "category": "crypto_catalyst",
                "headline": title,
                "body": body,
                "url": a.get("url", ""),
                "timestamp": a.get("seendate", datetime.utcnow().isoformat()),
                "raw_data": {
                    "domain": a.get("domain"),
                    "language": a.get("language"),
                    "socialimage": a.get("socialimage"),
                },
            })
        return signals
