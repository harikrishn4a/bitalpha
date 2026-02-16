"""Daily Update renderer — BTC price snapshot + news roundup (chains, digital assets, fintech)."""
from __future__ import annotations

from signal_engine.normalize import SignalItem
from utils.format import fmt_price, fmt_pct, inline_source


def render(
    *,
    date_str: str,
    # Price data
    price_usd: float, price_sgd: float | None,
    chg_24h: float | None, chg_7d: float | None,
    ath_usd: float | None,
    fng_value: int, fng_class: str,
    # News sections
    crypto_news: list[SignalItem],     # chains / digital asset news
    fintech_news: list[SignalItem],    # fintech stock news
    social_highlights: list[SignalItem],  # top X posts (optional)
    # Fintech movers
    fintech_movers: list[dict],
) -> str:
    L = []

    # ── Header ──
    L.append(f"**Crypto + FinTech Signal Intelligence — Daily Update**")
    L.append("")
    L.append(f"{date_str}")
    L.append("")

    # ── Price bar ──
    ath_line = ""
    if ath_usd:
        pct_ath = (price_usd - ath_usd) / ath_usd * 100
        if pct_ath < -5:
            ath_line = f" | Down ~{abs(pct_ath):.0f}% from ATH of ${fmt_price(ath_usd)}"
    L.append(f"**Price:** ${fmt_price(price_usd)} USD" + (f" / ${fmt_price(price_sgd)} SGD" if price_sgd else "") + ath_line)
    L.append(f"**Fear & Greed:** {fng_value} — {fng_class.upper()} | **24h:** {fmt_pct(chg_24h)} | **7d:** {fmt_pct(chg_7d)}")
    L.append("")
    L.append("---")
    L.append("")

    # ── Crypto / Digital Asset News ──
    L.append("**Crypto & Digital Assets**")
    L.append("")
    if crypto_news:
        for s in crypto_news[:6]:
            headline = s.headline.strip()
            body_text = (s.body or "").strip()
            # Truncate body to ~200 chars for readability
            if body_text and len(body_text) > 200:
                body_text = body_text[:197].rsplit(" ", 1)[0] + "..."
            if body_text and body_text != headline:
                L.append(f"• {headline}")
                L.append(f"  {body_text}")
                if s.url:
                    L.append(f"  [Read more]({s.url})")
            else:
                L.append(f"• {inline_source(headline, s.url)}")
            L.append("")
    else:
        L.append("• No major crypto news today.")
        L.append("")

    L.append("---")
    L.append("")

    # ── FinTech Stocks ──
    L.append("**FinTech Stocks**")
    L.append("")
    if fintech_movers:
        movers_line = []
        for m in fintech_movers[:6]:
            chg = m.get("chg_pct", 0)
            arrow = "▲" if chg >= 0 else "▼"
            sym = m["symbol"]
            price_str = f"${m['price']:,.2f}" if m.get("price") else "N/A"
            movers_line.append(f"**{sym}** {price_str} ({arrow} {abs(chg):.1f}%)")
        L.append(" | ".join(movers_line))
        L.append("")
    if fintech_news:
        for s in fintech_news[:5]:
            headline = s.headline.strip()
            body_text = (s.body or "").strip()
            if body_text and len(body_text) > 200:
                body_text = body_text[:197].rsplit(" ", 1)[0] + "..."
            if body_text and body_text != headline:
                L.append(f"• {headline}")
                L.append(f"  {body_text}")
                if s.url:
                    L.append(f"  [Read more]({s.url})")
            else:
                L.append(f"• {inline_source(headline, s.url)}")
            L.append("")
    elif not fintech_movers:
        L.append("• No fintech news today.")
        L.append("")

    # ── Social Buzz (optional, if any) ──
    if social_highlights:
        L.append("---")
        L.append("")
        L.append("**Trending on X**")
        L.append("")
        for s in social_highlights[:3]:
            text = s.headline.strip()
            eng = s.raw_data.get("engagement", 0) if s.raw_data else 0
            L.append(f"• {text}")
            if s.url:
                L.append(f"  [View]({s.url})" + (f" — {eng} engagements" if eng > 10 else ""))
            L.append("")

    L.append("---")
    L.append("")
    L.append("*Digital payment tokens are high-risk; this is informational, not financial advice.*")
    return "\n".join(L)
