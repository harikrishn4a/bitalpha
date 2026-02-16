"""BTC trend metrics: regime, levels, volatility, leverage flush proxy."""
from datetime import datetime

import pandas as pd


def _prices_df(market_chart: dict) -> pd.DataFrame:
    """Convert CoinGecko market_chart to DataFrame with daily prices."""
    rows = market_chart.get("prices", [])
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["ts", "price"])
    df["date"] = pd.to_datetime(df["ts"], unit="ms").dt.date
    daily = df.groupby("date")["price"].last().reset_index()
    daily["price"] = daily["price"].astype(float)
    return daily.sort_values("date").reset_index(drop=True)


def regime(df: pd.DataFrame, fng_value: int) -> str:
    """Panic if (7d vol > thresh OR 7d max dd > thresh) AND F&G < 20; Trend if price > 50d MA and 20d MA slope > 0; else Range."""
    if df.empty or len(df) < 50:
        return "Range"
    df = df.tail(90).copy()
    df["ma50"] = df["price"].rolling(50).mean()
    df["ma20"] = df["price"].rolling(20).mean()
    current = df.iloc[-1]
    price = current["price"]
    ma50 = current["ma50"]
    ma20_slope = df["ma20"].diff().iloc[-1] if len(df) >= 21 else 0
    # 7d realized vol (annualized): std of daily returns * sqrt(365)
    returns_7d = df["price"].pct_change().dropna().tail(7)
    vol_7d = returns_7d.std() * (365**0.5) * 100 if len(returns_7d) > 1 else 0
    high_7d = df["price"].tail(7).max()
    low_7d = df["price"].tail(7).min()
    dd_7d = (high_7d - low_7d) / high_7d * 100 if high_7d > 0 else 0
    if fng_value < 20 and (vol_7d > 80 or dd_7d > 15):
        return "Panic"
    if pd.notna(ma50) and price > ma50 and ma20_slope > 0:
        return "Trend"
    return "Range"


def levels(df: pd.DataFrame, current_price: float) -> dict:
    """Support1/2, Pivot, Resistance1/2 from last 14 days."""
    if df.empty:
        return {"support1": 0, "support2": 0, "pivot": round(current_price / 500) * 500, "resistance1": 0, "resistance2": 0}
    last14 = df.tail(14)
    lows = last14.nsmallest(2, "price")["price"].tolist()
    highs = last14.nlargest(2, "price")["price"].tolist()
    support1 = float(lows[0]) if lows else current_price * 0.95
    support2 = float(lows[1]) if len(lows) > 1 else support1 * 0.98
    resistance1 = float(highs[0]) if highs else current_price * 1.05
    resistance2 = float(highs[1]) if len(highs) > 1 else resistance1 * 1.02
    pivot = round(current_price / 500) * 500
    return {"support1": support1, "support2": support2, "pivot": pivot, "resistance1": resistance1, "resistance2": resistance2}


def pct_change_7d(df: pd.DataFrame) -> float | None:
    """7-day percent change."""
    if df.empty or len(df) < 8:
        return None
    p0 = df.iloc[-8]["price"]
    p1 = df.iloc[-1]["price"]
    if p0 == 0:
        return None
    return (p1 - p0) / p0 * 100


def pct_change_ytd(df: pd.DataFrame) -> float | None:
    """YTD percent change (vs Jan 1)."""
    if df.empty:
        return None
    year = df.iloc[-1]["date"].year if hasattr(df.iloc[-1]["date"], "year") else datetime.now().year
    jan1 = [r for r in df.itertuples() if getattr(r.date, "month", 1) == 1 and getattr(r.date, "year", 0) == year]
    if not jan1:
        return None
    p0 = jan1[0].price
    p1 = df.iloc[-1]["price"]
    if p0 == 0:
        return None
    return (p1 - p0) / p0 * 100


def leverage_flush_flag(df: pd.DataFrame, vol_24h_pct: float, volume_24h: float) -> bool:
    """Large 24h move + volume spike vs 30d avg -> possible leverage flush."""
    if df.empty or len(df) < 30:
        return False
    if abs(vol_24h_pct) < 5:
        return False
    # CoinGecko market_chart has total_volumes; use last 30 days avg
    return False  # Would need volumes in market_chart; skip for now or add if available


def historic_context(df: pd.DataFrame, ath_usd: float | None = None) -> dict:
    """Return 90d high/low, % from high, and ATH context for historic comparison."""
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


def interpret(regime: str, fng_val: int, fng_cls: str, chg_7d: float | None,
              pct_from_90d_high: float | None, macro_bullets: list[str]) -> list[str]:
    """Generate plain-English interpretation of what the numbers mean and what may be driving them."""
    bullets = []
    # Price move interpretation
    if chg_7d is not None:
        if chg_7d < -2:
            bullets.append(f"Price down {abs(chg_7d):.1f}% this week — likely profit-taking, macro headwinds, or sentiment reset.")
        elif chg_7d > 2:
            bullets.append(f"Price up {chg_7d:.1f}% this week — momentum or positive catalysts; watch for overextension.")
        else:
            bullets.append(f"Price relatively flat — consolidation; market digesting prior move.")
    # Fear & Greed interpretation
    if fng_val < 25:
        bullets.append(f"Fear & Greed at {fng_val} ({fng_cls}) — fear often marks local bottoms; contrarians watch for capitulation.")
    elif fng_val > 70:
        bullets.append(f"Fear & Greed at {fng_val} ({fng_cls}) — greed can precede pullbacks; position sizing matters.")
    # Regime
    if regime == "Panic":
        bullets.append("Regime: Panic — high vol + extreme fear; historically a setup for bounces, but timing is hard.")
    elif regime == "Trend":
        bullets.append("Regime: Trend — price above key MAs; trend followers are in; watch for exhaustion.")
    else:
        bullets.append("Regime: Range — no clear trend; levels matter; breakout above resistance or below support will matter.")
    # Macro (if available)
    if macro_bullets and "No strong macro" not in str(macro_bullets):
        bullets.append("Macro: " + "; ".join(macro_bullets[:2]))
    return bullets[:4]
