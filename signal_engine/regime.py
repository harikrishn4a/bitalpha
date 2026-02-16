"""Market regime detection: 6 tags + 5 macro drivers + weekly delta."""
from __future__ import annotations

import pandas as pd

REGIME_DEFINITIONS = {
    "Risk-on": "Markets favour risky assets; equities + crypto trend up on positive sentiment.",
    "Risk-off": "Flight to safety; USD/bonds strengthen, risk assets sell off.",
    "Trend": "BTC above key moving averages with positive slope; momentum-driven.",
    "Chop": "Range-bound, no clear direction; false breakouts likely.",
    "Squeeze": "Low volatility compressing; expect a large move soon (direction unclear).",
    "Breakdown": "Price below key support with accelerating selling; high vol.",
}


def prices_df(market_chart: dict) -> pd.DataFrame:
    """Convert CoinGecko market_chart to daily DataFrame."""
    rows = market_chart.get("prices", [])
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["ts", "price"])
    df["date"] = pd.to_datetime(df["ts"], unit="ms").dt.date
    daily = df.groupby("date")["price"].last().reset_index()
    daily["price"] = daily["price"].astype(float)
    return daily.sort_values("date").reset_index(drop=True)


def detect_regime(df: pd.DataFrame, fng_value: int,
                  dxy_chg: float | None = None, yields_chg: float | None = None) -> str:
    """Detect regime from price data + macro signals.

    Returns one of: Risk-on, Risk-off, Trend, Chop, Squeeze, Breakdown.
    """
    if df.empty or len(df) < 50:
        return "Chop"

    tail = df.tail(90).copy()
    tail["ma50"] = tail["price"].rolling(50, min_periods=30).mean()
    tail["ma20"] = tail["price"].rolling(20, min_periods=10).mean()

    current = tail.iloc[-1]
    price = current["price"]
    ma50 = current.get("ma50")
    ma20_slope = tail["ma20"].diff().iloc[-1] if len(tail) >= 21 else 0

    # Realized vol (7d annualized)
    returns_7d = tail["price"].pct_change().dropna().tail(7)
    vol_7d = returns_7d.std() * (365 ** 0.5) * 100 if len(returns_7d) > 1 else 0

    # Drawdown from 7d high
    high_7d = tail["price"].tail(7).max()
    low_7d = tail["price"].tail(7).min()
    dd_7d = (high_7d - low_7d) / high_7d * 100 if high_7d > 0 else 0

    # Bollinger bandwidth (squeeze detection)
    if len(tail) >= 20:
        bb_std = tail["price"].tail(20).std()
        bb_mean = tail["price"].tail(20).mean()
        bb_width = (bb_std / bb_mean * 100) if bb_mean else 999
    else:
        bb_width = 999

    # Breakdown: price < MA50 + high vol + extreme fear
    if pd.notna(ma50) and price < ma50 and vol_7d > 60 and fng_value < 25:
        return "Breakdown"

    # Squeeze: very low bandwidth
    if bb_width < 2.5 and vol_7d < 30:
        return "Squeeze"

    # Risk-off: USD strong + yields rising + fear
    if dxy_chg is not None and dxy_chg > 0.5 and fng_value < 35:
        return "Risk-off"

    # Risk-on: yields falling + greed + price above MAs
    if fng_value > 60 and pd.notna(ma50) and price > ma50:
        return "Risk-on"

    # Trend: price > MA50 + positive slope
    if pd.notna(ma50) and price > ma50 and ma20_slope > 0:
        return "Trend"

    return "Chop"


def compute_levels(df: pd.DataFrame, current_price: float) -> dict:
    """Support/resistance from last 14 days."""
    if df.empty:
        p = round(current_price / 500) * 500
        return {"S2": 0, "S1": 0, "Pivot": p, "R1": 0, "R2": 0}
    last14 = df.tail(14)
    lows = last14.nsmallest(2, "price")["price"].tolist()
    highs = last14.nlargest(2, "price")["price"].tolist()
    return {
        "S2": float(lows[1]) if len(lows) > 1 else float(lows[0]) * 0.98,
        "S1": float(lows[0]) if lows else current_price * 0.95,
        "Pivot": round(current_price / 500) * 500,
        "R1": float(highs[0]) if highs else current_price * 1.05,
        "R2": float(highs[1]) if len(highs) > 1 else float(highs[0]) * 1.02,
    }


def historic_context(df: pd.DataFrame, ath_usd: float | None = None) -> dict:
    """90d high/low, % from high, % from ATH."""
    out = {"high_90d": None, "low_90d": None, "pct_from_90d_high": None, "pct_from_ath": None}
    if df.empty or len(df) < 7:
        return out
    last90 = df.tail(90)
    high = float(last90["price"].max())
    low = float(last90["price"].min())
    current = float(df.iloc[-1]["price"])
    out["high_90d"] = high
    out["low_90d"] = low
    if high > 0:
        out["pct_from_90d_high"] = (current - high) / high * 100
    if ath_usd and ath_usd > 0:
        out["pct_from_ath"] = (current - ath_usd) / ath_usd * 100
    return out


def compute_delta(current: dict, previous: dict | None) -> str:
    """Compare current regime snapshot to previous. Return delta summary."""
    if not previous:
        return "First regime snapshot — no prior week to compare."
    parts = []
    cur_tag = current.get("regime_tag", "Chop")
    prev_tag = previous.get("regime_tag", "Chop")
    if cur_tag != prev_tag:
        parts.append(f"Regime shifted from {prev_tag} to {cur_tag}.")
    cur_d = current.get("drivers", {})
    prev_d = previous.get("drivers", {})
    for k in cur_d:
        cv = cur_d.get(k)
        pv = prev_d.get(k)
        if cv is not None and pv is not None:
            try:
                diff = float(cv) - float(pv)
                if abs(diff) > 0.1:
                    direction = "up" if diff > 0 else "down"
                    parts.append(f"{k}: {direction} ({diff:+.2f})")
            except (ValueError, TypeError):
                if str(cv) != str(pv):
                    parts.append(f"{k}: changed from {pv} to {cv}")
    return " | ".join(parts) if parts else "No significant changes vs last week."
