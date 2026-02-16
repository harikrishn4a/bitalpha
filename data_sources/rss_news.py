"""RSS-based crypto/fintech news from curated feeds."""
from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime

from .base import BaseSource

try:
    import feedparser
except ImportError:
    feedparser = None  # type: ignore


class RssNewsSource(BaseSource):
    """Fetch news from configured RSS feeds. Returns same raw signal shape as other sources."""
    name = "rss_news"
    _min_interval = 0.5

    def __init__(self, cache, feeds: list[dict]):
        super().__init__(cache)
        self.feeds = feeds  # list of {name, url, weight?}

    def fetch_signals(self) -> list[dict]:
        if not feedparser:
            return []
        signals = []
        for feed in self.feeds:
            name = feed.get("name", "rss")
            url = feed.get("url", "").strip()
            if not url:
                continue
            cached = self.cache.get("rss", url, None)
            if cached is not None:
                signals.extend(cached)
                continue
            self._rate_limit()
            try:
                resp = self.session.get(url, timeout=(5, 15))
                resp.raise_for_status()
                parsed = feedparser.parse(resp.content)
            except Exception:
                continue
            items = []
            for entry in parsed.entries[:15]:
                title = (entry.get("title") or "").strip()
                link = entry.get("link", "")
                if isinstance(link, dict):
                    link = link.get("href", "")
                if not title or not link:
                    continue
                summary = entry.get("summary", "") or entry.get("description", "")
                if isinstance(summary, dict):
                    summary = summary.get("value", "") or ""
                summary = (summary or "") if isinstance(summary, str) else ""
                if summary:
                    summary = summary.replace("<p>", " ").replace("</p>", " ").strip()
                published = entry.get("published", "") or entry.get("updated", "")
                try:
                    ts = parsedate_to_datetime(published).isoformat() if published else datetime.utcnow().isoformat()
                except Exception:
                    ts = datetime.utcnow().isoformat()
                raw = {
                    "source": self.name,
                    "category": "crypto_catalyst",
                    "headline": title,
                    "body": (summary or title)[:500],
                    "url": link,
                    "timestamp": ts,
                    "raw_data": {"feed_id": name},
                }
                items.append(raw)
            if items:
                self.cache.set("rss", url, items, None)
            signals.extend(items)
        return signals
