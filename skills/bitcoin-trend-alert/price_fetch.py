#!/usr/bin/env python3
"""Fetch BTC price and 24h/7d change from CoinGecko. Uses stdlib only (no requests)."""
import urllib.request
import json

r = urllib.request.urlopen(
    "https://api.coingecko.com/api/v3/coins/bitcoin",
    timeout=10,
)
data = json.loads(r.read().decode())
p = data["market_data"]
usd = p["current_price"].get("usd", "N/A")
sgd = p["current_price"].get("sgd", "N/A")
ch24 = p.get("price_change_percentage_24h")
ch7 = p.get("price_change_percentage_7d_in_currency", {}).get("sgd") or p.get(
    "price_change_percentage_7d"
)
print(f"BTC: ${usd} USD / ${sgd} SGD")
print(f"24h: {ch24 if ch24 is not None else 'N/A'}%")
print(f"7d: {ch7 if ch7 is not None else 'N/A'}%")
