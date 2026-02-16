"""FX rate: exchangerate.host or fallback to CoinGecko SGD/USD ratio."""
import requests
from ..config import EXCHANGERATE_API_KEY, COINGECKO_API_KEY
from ._cache import get_cached, set_cached
from . import coingecko

HEADERS = {"User-Agent": "btc_digest/1.0"}


def usd_sgd() -> float | None:
    """Return USD/SGD rate (1 USD = X SGD). Falls back to CoinGecko if FX API unavailable."""
    # Try exchangerate.host if key present
    if EXCHANGERATE_API_KEY:
        url = "https://api.exchangerate.host/latest"
        params = {"base": "USD", "symbols": "SGD", "access_key": EXCHANGERATE_API_KEY}
        cached = get_cached("fx", url, params)
        if cached is not None:
            return cached.get("rates", {}).get("SGD")
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            set_cached("fx", url, data, params)
            return data.get("rates", {}).get("SGD")
        except Exception:
            pass
    # Fallback: CoinGecko gives BTC in USD and SGD; SGD/USD = sgd/usd
    try:
        p = coingecko.simple_price(ids="bitcoin", vs_currencies="usd,sgd")
        btc = p.get("bitcoin", {})
        usd = btc.get("usd")
        sgd = btc.get("sgd")
        if usd and sgd and float(usd) > 0:
            return float(sgd) / float(usd)
    except Exception:
        pass
    return None
