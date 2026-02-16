"""Hourly news brief renderer — one message per item (short heading + Read More link)."""
from __future__ import annotations

import re

from signal_engine.normalize import SignalItem

# Max length for the displayed heading so messages stay clean and don't cut off
_MAX_HEADING_CHARS = 96


def _clean_heading(headline: str, body: str | None = None) -> str:
    """One-line summary/heading: flatten, truncate at word boundary, no mid-word breaks."""
    raw = (headline or "").strip()
    if (body or "").strip() and raw != (body or "").strip():
        # Prefer headline; if body is different and shorter, could use for summary
        pass
    # Flatten to one line: newlines and multiple spaces -> single space
    raw = re.sub(r"\s+", " ", raw).strip()
    # Optional: strip trailing hashtags so we don't end on "#crypto #news"
    raw = re.sub(r"\s+#\S+(\s+#\S+)*\s*$", "", raw).strip()
    if len(raw) <= _MAX_HEADING_CHARS:
        return raw
    # Truncate at last space before limit, add ellipsis
    cut = raw[:_MAX_HEADING_CHARS]
    last_space = cut.rfind(" ")
    if last_space > _MAX_HEADING_CHARS // 2:
        cut = cut[:last_space]
    return (cut.rstrip() + "\u2026") if cut else raw[:_MAX_HEADING_CHARS] + "\u2026"


def render(signals: list[SignalItem]) -> list[str] | None:
    """Render hourly news items as separate messages.

    Each message = short summary/heading (one line) + Read More link.
    Returns None if no signals.
    """
    if not signals:
        return None

    messages = []
    for s in signals:
        heading = _clean_heading(s.headline or "", s.body)
        if s.url:
            msg = f"**{heading}**\n\n[Read More]({s.url})"
        else:
            msg = f"**{heading}**"
        messages.append(msg)

    return messages
