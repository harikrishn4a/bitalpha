"""Generate weekly chart: 90d BTC price + 50d MA + last week H/L."""
from pathlib import Path

import pandas as pd

from ..config import OUTPUT_DIR, CHART_DIR, ensure_dirs
from ..apis import coingecko


def _prices_df(market_chart: dict) -> pd.DataFrame:
    rows = market_chart.get("prices", [])
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["ts", "price"])
    df["date"] = pd.to_datetime(df["ts"], unit="ms")
    daily = df.groupby(df["date"].dt.date)["price"].last().reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    daily["price"] = daily["price"].astype(float)
    return daily.sort_values("date").reset_index(drop=True)


def generate(output_path: Path | None = None) -> Path:
    """Create PNG chart. Returns path to saved file. Saves to CHART_DIR (often /tmp) so OpenClaw can attach it."""
    ensure_dirs()
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    out = output_path or (CHART_DIR / "btc_weekly_chart.png")
    data = coingecko.market_chart(days=90, vs_currency="usd")
    df = _prices_df(data)
    if df.empty or len(df) < 2:
        raise ValueError("Insufficient price data for chart")
    df["ma50"] = df["price"].rolling(50, min_periods=1).mean()
    last_week = df.tail(7)
    week_high = last_week["price"].max()
    week_low = last_week["price"].min()
    current_price = df.iloc[-1]["price"]
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["date"], df["price"], label="BTC (USD)", color="orange", linewidth=1.5)
    ax.plot(df["date"], df["ma50"], label="50d MA", color="blue", alpha=0.7, linewidth=1)
    ax.axhline(week_high, color="green", linestyle="--", alpha=0.5, label="Last week high")
    ax.axhline(week_low, color="red", linestyle="--", alpha=0.5, label="Last week low")
    ax.annotate(f"${current_price:,.0f}", xy=(df.iloc[-1]["date"], current_price), fontsize=9)
    ax.set_title("BTC (USD) — last 90d | Source: CoinGecko")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=100)
    plt.close()
    return out
