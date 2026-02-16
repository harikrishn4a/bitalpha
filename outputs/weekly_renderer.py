"""Weekly Macro Update renderer — narrative-driven 1-2-3 Digest + structured sections."""
from __future__ import annotations

from signal_engine.normalize import SignalItem
from signal_engine.regime import REGIME_DEFINITIONS
from utils.format import fmt_num, fmt_price, fmt_pct, inline_source


def render(
    *,
    date_str: str,
    # Narrative digest
    digest: dict,  # {"whats_happening": str, "why": list[str], "outlook": str}
    # A) Catalysts
    catalysts: list[SignalItem],
    # B) BTC snapshot
    price_usd: float, price_sgd: float | None,
    chg_7d: float | None, chg_ytd: float | None,
    ath_usd: float | None,
    fng_value: int, fng_class: str, fng_30d_range: str,
    levels: dict, regime: str,
    hist_context: dict,
    # C) Scenario
    scenario_base: str, scenario_bull: str, scenario_bear: str,
    # E) Fintech brief
    fintech_movers: list[dict],       # [{symbol, price, chg_pct, catalyst}]
    fintech_news: list[SignalItem],    # news that may drive moves
    # F) Exchange updates
    exchange_signals: list[SignalItem],
    # Macro
    macro_dashboard: list[str],
    macro_translation: list[str],
    macro_delta: str,
    # Regime
    regime_drivers: dict,
    # Learn
    learn_title: str, learn_body: str, learn_misconception: str,
) -> str:
    """Render the full weekly macro update."""
    L = []

    # ── Header ──
    L.append(f"# Crypto + FinTech Signal Intelligence — Weekly Update")
    L.append(f"**{date_str}**")
    L.append("")

    # ── Price bar ──
    ath_line = ""
    if ath_usd:
        pct_ath = (price_usd - ath_usd) / ath_usd * 100
        ath_line = f" | Down ~{abs(pct_ath):.0f}% from ATH of ${fmt_price(ath_usd)}"
    L.append(f"**Price:** ${fmt_price(price_usd)} USD" + (f" / ${fmt_price(price_sgd)} SGD" if price_sgd else "") + ath_line)
    L.append(f"**Fear & Greed:** {fng_value} — {fng_class.upper()}")
    L.append("")

    # ══ 1-2-3 Digest ══
    L.append("---")
    L.append("")
    L.append("## 1) What's happening?")
    L.append(digest["whats_happening"])
    L.append("")
    L.append("## 2) Why?")
    for b in digest["why"]:
        L.append(f"• {b}")
    L.append("")
    L.append("## 3) Historical parallels & outlook")
    L.append(digest["outlook"])
    L.append("")
    L.append("---")
    L.append("")

    # ── Market Regime ──
    L.append("## Market Regime")
    L.append(f"**{regime}** — {REGIME_DEFINITIONS.get(regime, '')}")
    if macro_delta:
        L.append(f"*What changed vs last week:* {macro_delta}")
    L.append("")

    # ── BTC Levels ──
    L.append("## BTC Levels")
    L.append(f"**7d:** {fmt_pct(chg_7d)} | **YTD:** {fmt_pct(chg_ytd)} | **30d F&G range:** {fng_30d_range}")
    h = hist_context
    if h.get("high_90d"):
        L.append(f"**90d range:** {fmt_num(h['low_90d'])} – {fmt_num(h['high_90d'])}")
    L.append(f"S2 {fmt_num(levels.get('S2'))} | S1 {fmt_num(levels.get('S1'))} | **Pivot {fmt_num(levels.get('Pivot'))}** | R1 {fmt_num(levels.get('R1'))} | R2 {fmt_num(levels.get('R2'))}")
    L.append("")

    # ── Dates to look out for ──
    L.append("## Dates to Look Out For")
    if catalysts:
        for c in catalysts[:10]:
            L.append(f"- **{c.timestamp[:10]}** — {inline_source(c.headline, c.url)}")
    else:
        L.append("- No upcoming catalysts in the next 14 days.")
    L.append("")

    # ── Scenario Simulation ──
    L.append("## Scenario Simulation")
    L.append(f"**Base case:** {scenario_base}")
    L.append(f"**Bull case:** {scenario_bull}")
    L.append(f"**Bear case:** {scenario_bear}")
    L.append("")

    # ── Macro Dashboard ──
    L.append("## Macro Dashboard")
    for line in macro_dashboard:
        L.append(line)
    L.append("")
    L.append("**Macro translation:**")
    for b in macro_translation:
        L.append(f"• {b}")
    L.append("")

    # ── Crypto/FinTech Stocks Brief ──
    L.append("## Crypto/FinTech Stocks Brief")
    if fintech_movers:
        L.append("**Watchlist:**")
        for m in fintech_movers[:6]:
            chg = m.get("chg_pct", 0)
            arrow = "▲" if chg >= 0 else "▼"
            sym = m["symbol"]
            price_str = f"${m['price']:,.2f}" if m.get("price") else "N/A"
            line = f"- **{sym}** {price_str} ({arrow} {abs(chg):.1f}%)"
            if m.get("catalyst"):
                line += f" — {m['catalyst']}"
            L.append(line)
        L.append("")
        if fintech_news:
            L.append("**Likely to move this week:**")
            for n in fintech_news[:5]:
                L.append(f"- {inline_source(n.headline, n.url)}")
            L.append("")
    else:
        L.append("- No significant fintech moves this week.")
        L.append("")

    # ── Exchange / New Firms ──
    L.append("## Exchange & Platform Updates")
    if exchange_signals:
        for s in exchange_signals[:5]:
            L.append(f"- {inline_source(s.headline, s.url)}")
    else:
        L.append("- No material exchange updates this week.")
    L.append("")

    # ── Learn ──
    L.append(f"**Learn:** {learn_title}")
    L.append(f"• {learn_body}")
    L.append(f"• Misconception: {learn_misconception}")
    L.append("")
    L.append("*Digital payment tokens are high-risk; this is informational, not financial advice.*")

    return "\n".join(L)
