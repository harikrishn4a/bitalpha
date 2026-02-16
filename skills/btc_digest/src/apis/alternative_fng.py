"""Alternative.me Fear & Greed Index API."""
import requests
from ._cache import get_cached, set_cached

BASE = "https://api.alternative.me/fng"
HEADERS = {"User-Agent": "btc_digest/1.0"}


def _get(limit: int = 1) -> dict:
    url = f"{BASE}/?limit={limit}"
    cached = get_cached("fng", url, None)
    if cached is not None:
        return cached
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()
    set_cached("fng", url, data, None)
    return data


def latest() -> dict:
    """Latest Fear & Greed value."""
    return _get(1)


def history(days: int = 30) -> dict:
    """Last N days of Fear & Greed."""
    return _get(days)
