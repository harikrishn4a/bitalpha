"""Assemble daily BTC 60-second brief."""
from datetime import datetime

from ..config import TIMEZONE, ensure_dirs
from ..apis import coingecko, alternative_fng
from ..analytics import btc_metrics
from . import macro_events

try:
    import zoneinfo
    tz = zoneinfo.ZoneInfo(TIMEZONE)
except ImportError:
    tz = None


def _now_sgt() -> datetime:
    if tz:
        return datetime.now(tz)
    return datetime.now()


def render() -> str:
    """Generate daily brief text."""
    ensure_dirs()
    now = _now_sgt()
    date_str = now.strftime("%a %d %b %Y")
    lines = []
    lines.append(f"# ₿ BTC 60-Second Brief — {date_str}")
    lines.append("")
    today_ev, upcoming_evs = macro_events.today_and_next(n=5, from_date=now)
    if today_ev or upcoming_evs:
        lines.append("## Important Dates — Macro Events")
        if today_ev:
            lines.append(f"**Today:** {today_ev.get('event', '')} ({today_ev.get('relevance', '')})")
        if upcoming_evs:
            lines.append("**Upcoming:**")
            for e in upcoming_evs:
                lines.append(f"- {e.get('date', '')} — {e.get('event', '')}")
        lines.append("")
    try:
        price_data = coingecko.simple_price(ids="bitcoin", vs_currencies="usd,sgd")
        btc = price_data.get("bitcoin", {})
        usd = btc.get("usd", "N/A")
        sgd = btc.get("sgd", "N/A")
    except Exception:
        usd = sgd = "N/A"
    try:
        coin = coingecko.coin_detail()
        md = coin.get("market_data", {})
        chg_24h = md.get("price_change_percentage_24h")
    except Exception:
        chg_24h = None
    try:
        fng = alternative_fng.latest()
        val = fng.get("data", [{}])[0].get("value", "N/A")
        cls = fng.get("data", [{}])[0].get("value_classification", "N/A")
    except Exception:
        val = cls = "N/A"
    try:
        mkt = coingecko.market_chart(days=30)
        df = btc_metrics._prices_df(mkt)
        current = float(df.iloc[-1]["price"]) if not df.empty else float(usd or 0)
        lvls = btc_metrics.levels(df, current)
    except Exception:
        lvls = {"support1": 0, "pivot": 0, "resistance1": 0}
    chg_str = f" | 24h: {chg_24h:+.1f}%" if chg_24h is not None else ""
    lines.append(f"**Price:** ${usd} USD / ${sgd} SGD{chg_str}")
    lines.append(f"**F&G:** {val} ({cls})")
    lines.append(f"**Levels:** S1 {lvls.get('support1', 0):,.0f} | Pivot {lvls.get('pivot', 0):,.0f} | R1 {lvls.get('resistance1', 0):,.0f}")
    lines.append("")
    lines.append("*Informational only — not financial advice.*")
    return "\n".join(lines)


def main():
    """Entry point for bin script."""
    import sys
    text = render()
    if "--print" in sys.argv or "-p" in sys.argv:
        print(text)
    else:
        from ..send import openclaw_send
        openclaw_send.send(text, None)
