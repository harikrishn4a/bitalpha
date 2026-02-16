"""Normalize raw API data into unified SignalItem schema."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SignalItem:
    """Unified signal representation across all sources."""
    id: str = ""
    source: str = ""
    category: str = ""         # macro, crypto_catalyst, on_chain, fintech, social
    headline: str = ""
    body: str = ""
    url: str = ""
    timestamp: str = ""
    raw_data: dict = field(default_factory=dict)
    # Scoring (filled by scoring.py)
    price_impact: int = 0      # 0-30
    novelty: int = 0           # 0-20
    credibility: int = 0       # 0-30
    time_sensitivity: int = 0  # 0-20
    signal_score: int = 0      # 0-100
    tier: str = "FYI"          # FYI | Heads Up | Actionable
    why_you_got_this: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "source": self.source, "category": self.category,
            "headline": self.headline, "body": self.body, "url": self.url,
            "timestamp": self.timestamp, "raw_data": self.raw_data,
            "price_impact": self.price_impact, "novelty": self.novelty,
            "credibility": self.credibility, "time_sensitivity": self.time_sensitivity,
            "signal_score": self.signal_score, "tier": self.tier,
            "why_you_got_this": self.why_you_got_this,
        }


def _make_id(source: str, url: str, headline: str) -> str:
    raw = f"{source}|{url}|{headline[:100]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def normalize_raw(raw_items: list[dict]) -> list[SignalItem]:
    """Convert a list of raw signal dicts (from any source) into SignalItem instances."""
    out = []
    for r in raw_items:
        item = SignalItem(
            id=_make_id(r.get("source", ""), r.get("url", ""), r.get("headline", "")),
            source=r.get("source", "unknown"),
            category=r.get("category", ""),
            headline=r.get("headline", ""),
            body=r.get("body", ""),
            url=r.get("url", ""),
            timestamp=r.get("timestamp", datetime.utcnow().isoformat()),
            raw_data=r.get("raw_data", {}),
        )
        out.append(item)
    return out
