"""NewsAPI connector for crypto/fintech news discovery."""
from __future__ import annotations

import os
from datetime import datetime, timedelta

from .base import BaseSource

_BASE = "https://newsapi.org/v2"

_DEFAULT_KEYWORDS = [
    "bitcoin", "crypto", "fintech", "stablecoin",
    "digital payments", "blockchain", "defi",
]


def _matches_keywords(text: str, keywords: list[str]) -> bool:
    """True if text (case-insensitive) contains at least one keyword."""
    if not keywords:
        return True
    lower = text.lower()
    return any(kw.lower() in lower for kw in keywords)


class NewsAPISource(BaseSource):
    name = "newsapi"
    _min_interval = 1.0

    def __init__(self, cache, api_key: str | None = None, keywords: list[str] | None = None,
                 filter_keywords: list[str] | None = None):
        super().__init__(cache)
        self.api_key = api_key or os.getenv("NEWSAPI_KEY", "")
        self.keywords = keywords or _DEFAULT_KEYWORDS
        self.filter_keywords = filter_keywords  # client-side: only keep articles matching these

    def fetch_articles(self, days_back: int = 2, page_size: int = 20) -> list[dict]:
        if not self.api_key:
            return []
        q = " OR ".join(self.keywords)
        from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        try:
            data = self._get(f"{_BASE}/everything", {
                "q": q,
                "from": from_date,
                "sortBy": "relevancy",
                "pageSize": str(page_size),
                "language": "en",
                "apiKey": self.api_key,
            }, cache_prefix="newsapi")
            return data.get("articles", [])
        except Exception:
            return []

    def fetch_signals(self) -> list[dict]:
        articles = self.fetch_articles()
        signals = []
        for a in articles:
            title = a.get("title", "")
            body = a.get("description", "") or a.get("content", "") or ""
            if self.filter_keywords and not _matches_keywords(title + " " + body, self.filter_keywords):
                continue
            signals.append({
                "source": "newsapi",
                "category": "crypto_catalyst",
                "headline": title,
                "body": body,
                "url": a.get("url", ""),
                "timestamp": a.get("publishedAt", datetime.utcnow().isoformat()),
                "raw_data": {
                    "author": a.get("author"),
                    "source_name": a.get("source", {}).get("name"),
                },
            })
        return signals
