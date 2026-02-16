"""Assemble weekly BTC Macro & Trend Pack. Returns (text, chart_path)."""
from datetime import datetime

import pandas as pd

from ..config import TIMEZONE, ensure_dirs
from ..apis import coingecko, alternative_fng, fred as fred_api, fx
from ..analytics import btc_metrics, macro_metrics, narrative
from ..charts import weekly_chart
from ..utils.format import fmt_num, fmt_price
from . import macro_events
from . import news as news_module

try:
    import zoneinfo
    tz = zoneinfo.ZoneInfo(TIMEZONE)
except ImportError:
    tz = None


def _now_sgt() -> datetime:
    if tz:
        return datetime.now(tz)
    return datetime.now()


def render() -> tuple[str, str | None]:
    """Generate weekly digest. Returns (text, chart_path)."""
    ensure_dirs()
    now = _now_sgt()
    date_str = now.strftime("%a %d %b %Y")
    time_str = now.strftime("%H:%M")
    lines = []
    # A) Header
    lines.append(f"# ₿ BTC Weekly Macro & Trend Pack — {date_str}, {time_str} SGT")
    lines.append("")
    # Price and F&G
    try:
        price_data = coingecko.simple_price(ids="bitcoin", vs_currencies="usd,sgd")
        btc = price_data.get("bitcoin", {})
        usd = btc.get("usd", "N/A")
        sgd = btc.get("sgd", "N/A")
    except Exception:
        usd = sgd = "N/A"
    usd_str = fmt_price(usd) if isinstance(usd, (int, float)) else str(usd)
    sgd_str = fmt_price(sgd) if isinstance(sgd, (int, float)) else str(sgd)
    try:
        coin = coingecko.coin_detail()
        md = coin.get("market_data", {})
        chg_24h = md.get("price_change_percentage_24h")
        chg_7d = md.get("price_change_percentage_7d")
    except Exception:
        chg_24h = chg_7d = None
    try:
        mkt = coingecko.market_chart(days=90)
        df = btc_metrics._prices_df(mkt)
        chg_7d = chg_7d or btc_metrics.pct_change_7d(df)
        chg_ytd = btc_metrics.pct_change_ytd(df)
    except Exception:
        chg_7d = chg_ytd = None
    lines.append(f"**Price now:** ${usd_str} USD / ${sgd_str} SGD")
    chg7 = f" ({chg_7d:+.1f}%)" if chg_7d is not None else ""
    chgytd = f" | YTD: {chg_ytd:+.1f}%" if chg_ytd is not None else ""
    lines.append(f"**7d change:**{chg7}{chgytd}")
    lines.append("")
    try:
        fng = alternative_fng.latest()
        data = fng.get("data", [{}])
        latest = data[0] if data else {}
        val = latest.get("value", "N/A")
        cls = latest.get("value_classification", "N/A")
        hist = alternative_fng.history(30)
        vals = [int(d["value"]) for d in hist.get("data", []) if d.get("value")]
        mn = min(vals) if vals else "N/A"
        mx = max(vals) if vals else "N/A"
        lines.append(f"**Fear & Greed:** {val} ({cls}) | 30d range: {mn}–{mx}")
    except Exception:
        lines.append("**Fear & Greed:** (unavailable)")
    lines.append("")
    # Historic context (90d range, ATH)
    hist = {}
    ath_usd = None
    try:
        mkt = coingecko.market_chart(days=90)
        df_hist = btc_metrics._prices_df(mkt)
        c = coingecko.coin_detail()
        ath_data = c.get("market_data", {}).get("ath", {})
        ath_usd = ath_data.get("usd") if isinstance(ath_data, dict) else None
        hist = btc_metrics.historic_context(df_hist, ath_usd)
    except Exception:
        pass
    if hist.get("high_90d") is not None and hist.get("low_90d") is not None:
        lines.append("**90d range:** " + fmt_num(hist["low_90d"]) + " – " + fmt_num(hist["high_90d"]))
        if hist.get("pct_from_90d_high") is not None:
            pct = hist["pct_from_90d_high"]
            lines.append(f"*{pct:+.1f}% from 90d high*" + (f" | {hist['pct_from_ath']:+.1f}% from ATH" if hist.get("pct_from_ath") is not None else ""))
        lines.append("")
    lines.append("---")
    lines.append("")
    # Important Dates (near top)
    evs = macro_events.upcoming(days=14)
    lines.append("## Important Dates — Macro Events")
    if evs:
        for e in evs[:14]:
            lines.append(f"- **{e.get('date', '')}** — {e.get('event', '')} ({e.get('relevance', '')})")
    else:
        lines.append("(No upcoming events in macro_events.json)")
    lines.append("")
    lines.append("---")
    lines.append("")
    # B) Trend Map
    try:
        mkt = coingecko.market_chart(days=90)
        df = btc_metrics._prices_df(mkt)
        fng_val = int(alternative_fng.latest().get("data", [{}])[0].get("value", 50))
        regime = btc_metrics.regime(df, fng_val)
        current = float(df.iloc[-1]["price"]) if not df.empty else float(usd)
        lvls = btc_metrics.levels(df, current)
        coin = coingecko.coin_detail()
        md = coin.get("market_data", {})
        vol24 = md.get("price_change_percentage_24h")
    except Exception:
        regime = "Range"
        lvls = {"support1": 0, "support2": 0, "pivot": 0, "resistance1": 0, "resistance2": 0}
        vol24 = None
    lines.append("## BTC Trend Map")
    lines.append(f"**Regime:** {regime}")
    lines.append(f"**Levels:** S2 {fmt_num(lvls['support2'])} | S1 {fmt_num(lvls['support1'])} | Pivot {fmt_num(lvls['pivot'])} | R1 {fmt_num(lvls['resistance1'])} | R2 {fmt_num(lvls['resistance2'])}")
    if vol24 is not None and abs(vol24) > 5:
        lines.append(f"*Large 24h move ({vol24:+.1f}%) — possible leverage flush/squeeze*")
    lines.append("")
    # C) Macro Dashboard
    lines.append("## Macro Dashboard")
    fred_data = None
    try:
        fred_data = fred_api.fetch_all()
    except Exception:
        pass
    for line in macro_metrics.format_macro(fred_data):
        lines.append(line)
    lines.append("")
    lines.append("**Macro translation:**")
    macro_bullets = macro_metrics.macro_translation(fred_data)
    for b in macro_bullets:
        lines.append(f"- {b}")
    lines.append("")
    # What it means (interpretation)
    fng_val, fng_cls = 50, "Neutral"
    try:
        fng_data = alternative_fng.latest().get("data", [{}])
        if fng_data:
            fng_val = int(fng_data[0].get("value", 50))
            fng_cls = fng_data[0].get("value_classification", "Neutral")
    except Exception:
        pass
    interp = btc_metrics.interpret(regime, fng_val, fng_cls, chg_7d, hist.get("pct_from_90d_high"), macro_bullets)
    lines.append("## What it means")
    for b in interp:
        lines.append(f"• {b}")
    lines.append("")
    # D) News
    lines.append("## Top Headlines")
    headlines = news_module.fetch_headlines(3)
    if headlines:
        for title, link in headlines:
            lines.append(f"- [{title}]({link})")
    else:
        lines.append("News disabled (no RSS sources configured).")
    lines.append("")
    # E) Learn 1 Thing
    title, analogy, misconception = narrative.learn_one_thing()
    lines.append("## Learn 1 Thing (90 seconds)")
    lines.append(f"**{title}**")
    lines.append(f"- {analogy}")
    lines.append(f"- Misconception to avoid: {misconception}")
    lines.append("")
    # F) Safety + MAS
    lines.append(f"**Safety tip:** {narrative.safety_tip()}")
    lines.append("")
    lines.append(f"*{narrative.mas_disclaimer()}*")
    text = "\n".join(lines)
    chart_path = None
    try:
        chart_path = str(weekly_chart.generate())
    except Exception:
        pass
    return text, chart_path


def main():
    """Entry point for bin script."""
    import sys
    text, chart_path = render()
    if "--print" in sys.argv or "-p" in sys.argv:
        print(text)
        if chart_path:
            print(f"\n[Chart saved to: {chart_path}]")
    else:
        from ..send import openclaw_send
        openclaw_send.send(text, chart_path)
