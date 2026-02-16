"""Tier classification: FYI / Heads Up / Actionable based on signal score."""
from __future__ import annotations

from .normalize import SignalItem

# Default thresholds (overridable via config)
_TIERS = {
    "Actionable": (80, 100),
    "Heads Up": (60, 79),
    "FYI": (0, 59),
}


def classify(item: SignalItem, thresholds: dict | None = None) -> SignalItem:
    """Assign tier based on signal_score. Mutates and returns item."""
    tiers = thresholds or _TIERS
    s = item.signal_score
    for tier_name, (lo, hi) in tiers.items():
        if lo <= s <= hi:
            item.tier = tier_name
            return item
    item.tier = "FYI"
    return item


def classify_batch(items: list[SignalItem], thresholds: dict | None = None) -> list[SignalItem]:
    """Classify all items."""
    return [classify(item, thresholds) for item in items]


def filter_by_tier(items: list[SignalItem], min_tier: str = "Heads Up") -> list[SignalItem]:
    """Return only items at or above min_tier."""
    order = {"FYI": 0, "Heads Up": 1, "Actionable": 2}
    min_level = order.get(min_tier, 1)
    return [i for i in items if order.get(i.tier, 0) >= min_level]
