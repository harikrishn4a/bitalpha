"""X (Twitter) trends connector: social signal layer."""
from __future__ import annotations

import os
from datetime import datetime

from .base import BaseSource

_BASE = "https://api.twitter.com/2"

# Market-moving query: catches price action, macro reactions, and institutional moves
_DEFAULT_QUERY = (
    '(bitcoin OR BTC) '
    '(rally OR crash OR dump OR breakout OR breakdown OR liquidation OR '
    '"all time high" OR ATH OR ETF OR "rate cut" OR CPI OR FOMC OR '
    'accumulation OR whale OR inflow OR outflow OR dominance OR halving) '
    'lang:en -is:retweet -is:reply'
)

# Minimum engagement to filter spam (likes + RTs + replies)
_MIN_ENGAGEMENT = 2


class XTrendsSource(BaseSource):
    name = "x_trends"
    _min_interval = 1.0

    def __init__(self, cache, bearer_token: str | None = None):
        super().__init__(cache)
        self.bearer = bearer_token or os.getenv("X_BEARER_TOKEN", "")

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.bearer}"}

    def search_recent(self, query: str | None = None,
                      max_results: int = 50) -> list[dict]:
        """Search recent tweets. Fetches more, then filters by engagement."""
        if not self.bearer:
            return []
        q = query or _DEFAULT_QUERY
        try:
            data = self._get(
                f"{_BASE}/tweets/search/recent",
                params={
                    "query": q,
                    "max_results": str(min(max_results, 100)),
                    "tweet.fields": "created_at,public_metrics,author_id",
                },
                headers=self._auth_headers(),
                cache_prefix="xtrends",
            )
            tweets = data.get("data", [])
            # Sort by engagement and filter spam
            for t in tweets:
                m = t.get("public_metrics", {})
                t["_engagement"] = (
                    m.get("retweet_count", 0)
                    + m.get("like_count", 0)
                    + m.get("reply_count", 0)
                )
            tweets.sort(key=lambda t: t["_engagement"], reverse=True)
            return tweets
        except Exception:
            return []

    def tweet_counts(self, query: str = "bitcoin") -> list[dict]:
        """Get tweet volume counts (available on Basic tier). Useful for sentiment proxy."""
        if not self.bearer:
            return []
        try:
            data = self._get(
                f"{_BASE}/tweets/counts/recent",
                params={"query": query},
                headers=self._auth_headers(),
                cache_prefix="xtrends_counts",
            )
            return data.get("data", [])
        except Exception:
            return []

    def fetch_signals(self) -> list[dict]:
        tweets = self.search_recent()
        signals = []

        # Also get volume trend for context
        counts = self.tweet_counts("bitcoin")
        vol_trend = None
        if len(counts) >= 48:  # 2 days of hourly data
            recent_24h = sum(c.get("tweet_count", 0) for c in counts[-24:])
            prev_24h = sum(c.get("tweet_count", 0) for c in counts[-48:-24])
            if prev_24h > 0:
                vol_trend = (recent_24h - prev_24h) / prev_24h * 100

        for t in tweets:
            engagement = t.get("_engagement", 0)
            # Skip very low engagement tweets
            if engagement < _MIN_ENGAGEMENT:
                continue
            metrics = t.get("public_metrics", {})
            signals.append({
                "source": "x_trends",
                "category": "social",
                "headline": t.get("text", "")[:140],
                "body": t.get("text", ""),
                "url": f"https://x.com/i/web/status/{t.get('id', '')}",
                "timestamp": t.get("created_at", datetime.utcnow().isoformat()),
                "raw_data": {
                    "tweet_id": t.get("id"),
                    "author_id": t.get("author_id"),
                    "engagement": engagement,
                    "metrics": metrics,
                    "btc_tweet_volume_trend_pct": vol_trend,
                },
            })

        # If all tweets were below threshold, take top 5 by engagement anyway
        if not signals and tweets:
            for t in tweets[:5]:
                metrics = t.get("public_metrics", {})
                signals.append({
                    "source": "x_trends",
                    "category": "social",
                    "headline": t.get("text", "")[:140],
                    "body": t.get("text", ""),
                    "url": f"https://x.com/i/web/status/{t.get('id', '')}",
                    "timestamp": t.get("created_at", datetime.utcnow().isoformat()),
                    "raw_data": {
                        "tweet_id": t.get("id"),
                        "author_id": t.get("author_id"),
                        "engagement": t.get("_engagement", 0),
                        "metrics": metrics,
                        "btc_tweet_volume_trend_pct": vol_trend,
                    },
                })

        return signals
