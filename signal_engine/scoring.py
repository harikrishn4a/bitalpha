"""Deterministic signal scoring: price_impact + novelty + credibility + time_sensitivity = 0-100."""
from __future__ import annotations

from datetime import datetime, timedelta

from .normalize import SignalItem

# Source credibility ratings (0-30 scale)
_CREDIBILITY = {
    "fred": 28,
    "coingecko": 25,
    "coinmarketcal": 18,
    "finnhub": 22,
    "newsapi": 15,
    "gdelt": 12,
    "x_trends": 8,
}

# Category base price_impact (0-30 scale, adjusted by content)
_CATEGORY_IMPACT = {
    "macro": 20,
    "crypto_catalyst": 18,
    "on_chain": 15,
    "fintech": 12,
    "social": 5,
}


def _score_price_impact(item: SignalItem) -> int:
    """Score price impact 0-30 based on category + content signals."""
    base = _CATEGORY_IMPACT.get(item.category, 10)
    rd = item.raw_data
    # BTC price move amplifier
    chg = abs(rd.get("chg_24h", 0) or 0)
    if chg > 5:
        base = min(30, base + 8)
    elif chg > 2:
        base = min(30, base + 4)
    # FRED series: rate/yield changes
    if item.source == "fred" and "observations" in rd:
        obs = rd["observations"]
        if len(obs) >= 2:
            try:
                v0, v1 = float(obs[1]["value"]), float(obs[0]["value"])
                if abs(v1 - v0) / max(abs(v0), 0.01) > 0.05:
                    base = min(30, base + 6)
            except (ValueError, KeyError):
                pass
    # Finnhub large stock moves
    if item.source == "finnhub":
        dp = abs(rd.get("dp", 0) or 0)
        if dp > 5:
            base = min(30, base + 6)
        elif dp > 2:
            base = min(30, base + 3)
    # F&G extremes
    fng = rd.get("fng_value")
    if fng is not None:
        try:
            v = int(fng)
            if v <= 10 or v >= 90:
                base = min(30, base + 8)
            elif v <= 25 or v >= 75:
                base = min(30, base + 4)
        except (ValueError, TypeError):
            pass
    # Social engagement amplifier
    if item.source == "x_trends":
        eng = rd.get("engagement", 0)
        if eng > 10000:
            base = min(30, base + 10)
        elif eng > 1000:
            base = min(30, base + 5)
    return min(30, max(0, base))


def _score_novelty(item: SignalItem) -> int:
    """Score novelty 0-20. New events / catalysts score higher than recurring data."""
    if item.category == "crypto_catalyst":
        return 18
    if item.source in ("newsapi", "gdelt"):
        return 16
    if item.source == "x_trends":
        return 14
    if item.source == "finnhub" and "headline" in item.raw_data:
        return 15
    # Recurring macro data
    if item.source == "fred" and "observations" in item.raw_data:
        return 6
    # Price snapshots are not novel
    if item.source == "coingecko" and "price_usd" in item.raw_data:
        return 4
    return 10


def _score_credibility(item: SignalItem) -> int:
    """Score source credibility 0-30."""
    return _CREDIBILITY.get(item.source, 10)


def _score_time_sensitivity(item: SignalItem) -> int:
    """Score time sensitivity 0-20 based on how soon the event matters."""
    # Upcoming events within 48h are most time-sensitive
    try:
        ts = datetime.fromisoformat(item.timestamp.replace("Z", "+00:00"))
        now = datetime.utcnow()
        if hasattr(ts, "tzinfo") and ts.tzinfo:
            now = now.replace(tzinfo=ts.tzinfo)
        delta = ts - now
        if timedelta(0) <= delta <= timedelta(hours=24):
            return 20
        if timedelta(0) <= delta <= timedelta(hours=48):
            return 16
        if timedelta(0) <= delta <= timedelta(days=7):
            return 10
    except (ValueError, TypeError):
        pass
    # Breaking news / social spikes
    if item.source in ("newsapi", "gdelt", "x_trends"):
        return 14
    # Macro data just released
    if item.source == "fred":
        return 8
    return 6


def _top_contributors(item: SignalItem) -> list[str]:
    """Return the top 2 score contributors as 'why you got this' bullets."""
    scores = {
        "Price impact": item.price_impact,
        "Novelty": item.novelty,
        "Credibility": item.credibility,
        "Time sensitivity": item.time_sensitivity,
    }
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [f"{k}: {v}/{w}" for k, v in ranked[:2]
            for w in [{"Price impact": 30, "Novelty": 20, "Credibility": 30, "Time sensitivity": 20}[k]]]


def score(item: SignalItem) -> SignalItem:
    """Compute all scores for a SignalItem. Mutates and returns the item."""
    item.price_impact = _score_price_impact(item)
    item.novelty = _score_novelty(item)
    item.credibility = _score_credibility(item)
    item.time_sensitivity = _score_time_sensitivity(item)
    item.signal_score = (
        item.price_impact + item.novelty + item.credibility + item.time_sensitivity
    )
    item.why_you_got_this = _top_contributors(item)
    return item


def score_batch(items: list[SignalItem]) -> list[SignalItem]:
    """Score all items and sort by signal_score descending."""
    scored = [score(item) for item in items]
    scored.sort(key=lambda x: x.signal_score, reverse=True)
    return scored
