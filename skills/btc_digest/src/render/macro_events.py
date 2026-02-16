"""Load and filter macro_events.json."""
import json
from datetime import datetime, timedelta
from pathlib import Path

from ..config import MACRO_EVENTS_PATH


def load() -> list[dict]:
    """Load macro_events.json. Returns [] if missing or invalid."""
    if not MACRO_EVENTS_PATH.exists():
        return []
    try:
        with open(MACRO_EVENTS_PATH) as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []
    if not isinstance(data, list):
        return []
    return data


def _parse_date(s: str) -> datetime | None:
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def upcoming(days: int = 14, from_date: datetime | None = None) -> list[dict]:
    """Events from today through the next N days."""
    today = (from_date or datetime.now()).date()
    end = today + timedelta(days=days)
    out = []
    for ev in load():
        d = _parse_date(ev.get("date", ""))
        if d and today <= d.date() <= end:
            out.append({**ev, "date": d.strftime("%Y-%m-%d")})
    out.sort(key=lambda x: x.get("date", ""))
    return out


def today_and_next(n: int = 5, from_date: datetime | None = None) -> tuple[dict | None, list[dict]]:
    """(today's event if any, next N upcoming)."""
    evs = upcoming(days=n + 7, from_date=from_date)
    today_str = (from_date or datetime.now()).strftime("%Y-%m-%d")
    today_ev = next((e for e in evs if e.get("date") == today_str), None)
    future = [e for e in evs if e.get("date", "") > today_str][:n]
    return today_ev, future
