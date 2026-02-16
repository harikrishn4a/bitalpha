"""5 macro drivers tracking + translation for the weekly regime layer."""
from __future__ import annotations

_SERIES_LABELS = {
    "DGS10": "10Y yield",
    "DGS2": "2Y yield",
    "DTWEXBGS": "Dollar index (DXY proxy)",
    "T10Y2Y": "10-2 spread",
    "ICSA": "Initial claims",
    "CPIAUCSL": "CPI",
    "FEDFUNDS": "Fed funds rate",
}


def format_dashboard(fred_data: dict[str, list[dict]] | None,
                     global_crypto: dict | None = None,
                     etf_flows: dict | None = None) -> list[str]:
    """Format macro dashboard with FRED series + crypto market breadth + ETF flows."""
    lines = []

    # FRED series
    if fred_data:
        for sid, label in _SERIES_LABELS.items():
            obs = fred_data.get(sid, [])
            if not obs:
                continue
            latest = next((o for o in obs if o.get("value") not in (".", None, "")), None)
            prev = next((o for o in obs[1:] if o.get("value") not in (".", None, "")), None)
            if not latest:
                continue
            val = latest["value"]
            line = f"- {label}: {val}"
            if prev:
                try:
                    chg = float(latest["value"]) - float(prev["value"])
                    line += f" (WoW {chg:+.2f})"
                except (ValueError, TypeError):
                    pass
            lines.append(line)
    else:
        lines.append("- (FRED data unavailable — check FRED_API_KEY or network)")

    # Crypto market breadth (from CoinGecko global)
    if global_crypto:
        dom = global_crypto.get("market_cap_percentage", {}).get("btc")
        total_vol = global_crypto.get("total_volume", {}).get("usd")
        total_mcap = global_crypto.get("total_market_cap", {}).get("usd")
        if dom is not None:
            lines.append(f"- BTC dominance: {dom:.1f}%")
        if total_vol:
            lines.append(f"- Crypto 24h volume: ${total_vol / 1e9:,.1f}B")
        if total_mcap:
            lines.append(f"- Total crypto market cap: ${total_mcap / 1e12:,.2f}T")

    # ETF flows (placeholder — add source when available)
    if etf_flows:
        net = etf_flows.get("netFlow")
        if net is not None:
            direction = "inflow" if net > 0 else "outflow"
            lines.append(f"- BTC ETF net {direction}: ${abs(net):,.0f}M")

    return lines or ["(Dashboard data unavailable)"]


def extract_drivers(fred_data: dict[str, list[dict]] | None) -> dict:
    """Extract the 5 macro driver values for regime computation."""
    drivers = {
        "usd_strength": None,
        "rates_yields": None,
        "equities_risk": None,
        "liquidity": None,
        "geopolitical": None,
    }
    if not fred_data:
        return drivers
    # USD strength = DXY proxy
    dxy = fred_data.get("DTWEXBGS", [])
    if dxy and dxy[0].get("value") not in (".", None, ""):
        drivers["usd_strength"] = float(dxy[0]["value"])
    # Rates = 10Y yield
    y10 = fred_data.get("DGS10", [])
    if y10 and y10[0].get("value") not in (".", None, ""):
        drivers["rates_yields"] = float(y10[0]["value"])
    # Liquidity = fed funds as proxy
    ff = fred_data.get("FEDFUNDS", [])
    if ff and ff[0].get("value") not in (".", None, ""):
        drivers["liquidity"] = float(ff[0]["value"])
    return drivers


def macro_translation(fred_data: dict[str, list[dict]] | None) -> list[str]:
    """Generate 2-3 macro translation bullets."""
    if not fred_data:
        return ["Add FRED_API_KEY for macro translation."]
    bullets = []
    # Yields
    dgs = fred_data.get("DGS10", [])
    if len(dgs) >= 2:
        try:
            cur, prev = float(dgs[0]["value"]), float(dgs[1]["value"])
            if cur - prev > 0.1:
                bullets.append(f"10Y yields rising ({prev:.2f} -> {cur:.2f}) — headwind for risk assets, higher discount rate.")
            elif prev - cur > 0.1:
                bullets.append(f"10Y yields falling ({prev:.2f} -> {cur:.2f}) — tailwind for risk assets, easing expectations.")
        except (ValueError, KeyError):
            pass
    # Dollar
    dxy = fred_data.get("DTWEXBGS", [])
    if len(dxy) >= 2:
        try:
            cur, prev = float(dxy[0]["value"]), float(dxy[1]["value"])
            if cur - prev > 0.3:
                bullets.append(f"USD strengthening ({prev:.1f} -> {cur:.1f}) — risk-off pressure, crypto historically weakens.")
            elif prev - cur > 0.3:
                bullets.append(f"USD weakening ({prev:.1f} -> {cur:.1f}) — risk-on tailwind, liquidity loosening.")
        except (ValueError, KeyError):
            pass
    # Claims + yields combo
    icsa = fred_data.get("ICSA", [])
    if len(icsa) >= 2 and len(dgs) >= 2:
        try:
            ic_cur, ic_prev = float(icsa[0]["value"]), float(icsa[1]["value"])
            y_cur, y_prev = float(dgs[0]["value"]), float(dgs[1]["value"])
            if ic_cur > ic_prev and y_cur < y_prev:
                bullets.append("Claims rising + yields falling — market pricing rate cuts; watch for risk rally.")
        except (ValueError, KeyError):
            pass
    if not bullets:
        bullets.append("No strong macro signals this week — regime steady.")
    return bullets[:3]
