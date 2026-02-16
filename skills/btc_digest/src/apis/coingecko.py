"""CoinGecko API client. Uses free endpoints; supports Pro API key header if set."""
import requests
from ..config import COINGECKO_API_KEY
from ._cache import get_cached, set_cached

BASE = "https://api.coingecko.com/api/v3"
HEADERS = {"User-Agent": "btc_digest/1.0"}
if COINGECKO_API_KEY:
    HEADERS["x-cg-pro-api-key"] = COINGECKO_API_KEY


def _get(url: str, params: dict | None = None) -> dict | list:
    cached = get_cached("cg", url, params)
    if cached is not None:
        return cached
    r = requests.get(url, headers=HEADERS, params=params or {}, timeout=30)
    r.raise_for_status()
    data = r.json()
    set_cached("cg", url, data, params)
    return data


def simple_price(ids: str = "bitcoin", vs_currencies: str = "usd,sgd") -> dict:
    """Fetch /simple/price."""
    url = f"{BASE}/simple/price"
    return _get(url, {"ids": ids, "vs_currencies": vs_currencies})


def coin_detail() -> dict:
    """Fetch /coins/bitcoin with market_data."""
    url = f"{BASE}/coins/bitcoin"
    return _get(url, {"localization": "false", "tickers": "false", "community_data": "false", "developer_data": "false"})


def market_chart(days: int = 90, vs_currency: str = "usd") -> dict:
    """Fetch /coins/bitcoin/market_chart."""
    url = f"{BASE}/coins/bitcoin/market_chart"
    return _get(url, {"vs_currency": vs_currency, "days": str(days)})
