"""Open-ended chart generation using matplotlib."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from signal_engine.regime import prices_df
from utils.format import fmt_num


def _base_style(ax):
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=8)


def generate_btc_price_ma(market_chart: dict, output_path: Path) -> Path:
    """90d BTC price + 50d MA + 20d MA + last-week high/low."""
    df = prices_df(market_chart)
    if df.empty or len(df) < 2:
        raise ValueError("Insufficient data for chart")
    df["date"] = pd.to_datetime(df["date"])
    df["ma50"] = df["price"].rolling(50, min_periods=1).mean()
    df["ma20"] = df["price"].rolling(20, min_periods=1).mean()
    last_week = df.tail(7)
    wh, wl = last_week["price"].max(), last_week["price"].min()
    cur = df.iloc[-1]["price"]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["date"], df["price"], label="BTC (USD)", color="orange", lw=1.5)
    ax.plot(df["date"], df["ma50"], label="50d MA", color="blue", alpha=0.7, lw=1)
    ax.plot(df["date"], df["ma20"], label="20d MA", color="purple", alpha=0.5, lw=1)
    ax.axhline(wh, color="green", ls="--", alpha=0.5, label=f"Week High {fmt_num(wh)}")
    ax.axhline(wl, color="red", ls="--", alpha=0.5, label=f"Week Low {fmt_num(wl)}")
    ax.annotate(f"${cur:,.0f}", xy=(df.iloc[-1]["date"], cur), fontsize=9,
                fontweight="bold", color="orange")
    ax.set_title("BTC (USD) — 90d Price + Moving Averages")
    ax.set_ylabel("Price (USD)")
    _base_style(ax)
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)
    return output_path


def generate_volatility_atr(market_chart: dict, output_path: Path) -> Path:
    """ATR / realized volatility chart."""
    df = prices_df(market_chart)
    if df.empty or len(df) < 14:
        raise ValueError("Insufficient data for vol chart")
    df["date"] = pd.to_datetime(df["date"])
    df["returns"] = df["price"].pct_change()
    df["vol_14d"] = df["returns"].rolling(14).std() * (365 ** 0.5) * 100

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True,
                                    gridspec_kw={"height_ratios": [2, 1]})
    ax1.plot(df["date"], df["price"], color="orange", lw=1.5, label="BTC Price")
    ax1.set_ylabel("Price (USD)")
    ax1.set_title("BTC Price vs 14d Realized Volatility")
    _base_style(ax1)

    ax2.fill_between(df["date"], df["vol_14d"], alpha=0.4, color="red", label="14d Vol (ann.)")
    ax2.set_ylabel("Vol (%)")
    _base_style(ax2)
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)
    return output_path


def generate_fear_greed_vs_price(market_chart: dict, fng_history: dict,
                                  output_path: Path) -> Path:
    """Overlay F&G index on BTC price."""
    df = prices_df(market_chart)
    if df.empty:
        raise ValueError("Insufficient data")
    df["date"] = pd.to_datetime(df["date"])
    fng_data = fng_history.get("data", [])
    if not fng_data:
        raise ValueError("No F&G data")

    fng_df = pd.DataFrame([
        {"date": pd.Timestamp.now() - pd.Timedelta(days=int(d.get("timestamp", "0")) // 86400 if False else i),
         "fng": int(d["value"])}
        for i, d in enumerate(fng_data)
    ])
    # Simpler: use index order (most recent first)
    fng_df = pd.DataFrame(fng_data)
    fng_df["fng"] = fng_df["value"].astype(int)
    fng_df = fng_df.iloc[::-1].reset_index(drop=True)
    fng_df["idx"] = range(len(fng_df))

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(df["date"].tail(len(fng_df)), df["price"].tail(len(fng_df)),
             color="orange", lw=1.5, label="BTC Price")
    ax1.set_ylabel("Price (USD)")
    ax2 = ax1.twinx()
    ax2.bar(df["date"].tail(len(fng_df)), fng_df["fng"].values[:len(df.tail(len(fng_df)))],
            alpha=0.3, color="blue", label="F&G Index")
    ax2.set_ylabel("Fear & Greed (0-100)")
    ax1.set_title("BTC Price vs Fear & Greed Index")
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)
    return output_path


# Chart type registry
CHART_GENERATORS = {
    "btc_price_ma": generate_btc_price_ma,
    "volatility_atr": generate_volatility_atr,
    "fear_greed_vs_price": generate_fear_greed_vs_price,
}
