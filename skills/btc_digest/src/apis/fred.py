"""FRED API client. Returns None if FRED_API_KEY not set."""
import requests
from ..config import FRED_API_KEY
from ._cache import get_cached, set_cached

BASE = "https://api.stlouisfed.org/fred/series/observations"
HEADERS = {"User-Agent": "btc_digest/1.0"}

# Series requested by spec
SERIES = {
    "DGS10": "10Y Treasury yield",
    "DTWEXBGS": "Broad USD index",
    "T10Y2Y": "10-2 spread",
    "ICSA": "Initial claims",
    "CPIAUCSL": "CPI",
    "FEDFUNDS": "Fed funds rate",
}


def fetch_series(series_id: str, limit: int = 2) -> list[dict] | None:
    """Fetch latest observations for a FRED series. Returns None if no API key."""
    if not FRED_API_KEY:
        return None
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": str(limit),
    }
    url = BASE
    cached = get_cached("fred", url, params)
    if cached is not None:
        return cached.get("observations", [])
    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    set_cached("fred", url, data, params)
    return data.get("observations", [])


def fetch_all() -> dict[str, list[dict]] | None:
    """Fetch latest + prior for all series. Returns None if FRED unavailable."""
    if not FRED_API_KEY:
        return None
    out = {}
    for sid in SERIES:
        try:
            obs = fetch_series(sid, limit=5)
            if obs:
                out[sid] = obs
        except Exception:
            pass
    return out if out else None
