"""Hash-based deduplication of signals."""
from __future__ import annotations

from .normalize import SignalItem


def dedupe(items: list[SignalItem], seen_ids: set[str]) -> list[SignalItem]:
    """Remove items whose ID is already in seen_ids. Returns fresh items only."""
    fresh = []
    for item in items:
        if item.id not in seen_ids:
            seen_ids.add(item.id)
            fresh.append(item)
    return fresh
