"""Weekly Macro Update renderer — laser focus: Bitcoin, macro, policy, regulation, analyst views, key dates."""
from __future__ import annotations

from signal_engine.normalize import SignalItem
from signal_engine.regime import REGIME_DEFINITIONS
from utils.format import fmt_num, fmt_price, fmt_pct, inline_source


def render(
    *,
    date_str: str,
    # Narrative digest
    digest: dict,  # {"whats_happening": str, "why": list[str], "outlook": str}
    # Catalysts (FRED / calendar) + key events (policy, legal, meetings from news)
    catalysts: list[SignalItem],
    key_events: list[SignalItem],
    # BTC snapshot (single place: levels only; price is in digest narrative)
    price_usd: float,
    price_sgd: float | None,
    chg_7d: float | None,
    chg_ytd: float | None,
    ath_usd: float | None,
    fng_value: int,
    fng_class: str,
    fng_30d_range: str,
    levels: dict,
    regime: str,
    hist_context: dict,
    # Scenario
    scenario_base: str,
    scenario_bull: str,
    scenario_bear: str,
    # Macro (expanded)
    macro_dashboard: list[str],
    macro_translation: list[str],
    macro_delta: str,
    regime_drivers: dict,
    # Policy & regulation, analyst / leading voices
    policy_regulation: list[SignalItem],
    analyst_voices: list[SignalItem],
) -> str:
    """Render the weekly update: Bitcoin, macro, policy, regulation, analysts, key dates."""
    L = []

    # ── Header (no duplicate price bar; price lives in 1) What's happening?) ──
    L.append(f"# Pocket Intelligence Weekly Update")
    L.append(f"**{date_str}**")
    L.append("")
    L.append("---")
    L.append("")

    # ══ 1-2-3 Digest (Bitcoin narrative — single place for price context) ══
    L.append("## **1) What's happening?**")
    L.append(digest["whats_happening"])
    L.append("")
    L.append("## **2) Why?**")
    for b in digest["why"]:
        L.append(f"• {b}")
    L.append("")
    L.append("## **3) Historical parallels & outlook**")
    L.append(digest["outlook"])
    L.append("")
    L.append("---")
    L.append("")

    # ── Market Regime ──
    L.append("## **Market Regime**")
    L.append(f"**{regime}** — {REGIME_DEFINITIONS.get(regime, '')}")
    if macro_delta:
        L.append(f"*What changed vs last week:* {macro_delta}")
    L.append("")

    # ── BTC Levels (one place for levels; no repeated price) ──
    L.append("## **BTC Levels**")
    L.append(f"**7d:** {fmt_pct(chg_7d)} | **YTD:** {fmt_pct(chg_ytd)} | **30d F&G range:** {fng_30d_range}")
    h = hist_context
    if h.get("high_90d"):
        L.append(f"**90d range:** {fmt_num(h['low_90d'])} – {fmt_num(h['high_90d'])}")
    L.append(f"S2 {fmt_num(levels.get('S2'))} | S1 {fmt_num(levels.get('S1'))} | **Pivot {fmt_num(levels.get('Pivot'))}** | R1 {fmt_num(levels.get('R1'))} | R2 {fmt_num(levels.get('R2'))}")
    L.append("")

    # ── Key dates & events (FRED/calendar + policy/legal/meetings from news) ──
    L.append("## **Key dates & events**")
    has_any = False
    if catalysts:
        for c in catalysts[:10]:
            date_part = (c.timestamp or "")[:10]
            prefix = f"- **{date_part}** — " if date_part else "- "
            suffix = ". Source: FRED" if c.source == "fred" else (f" [Link]({c.url})" if c.url else "")
            L.append(f"{prefix}{c.headline.strip()}{suffix}")
            has_any = True
    for e in key_events[:8]:
        L.append(f"- {inline_source(e.headline.strip(), e.url)}")
        has_any = True
    if not has_any:
        L.append("- No upcoming catalysts or key events in the next 14 days.")
    L.append("")

    # ── Scenario Simulation ──
    L.append("## **Scenario Simulation**")
    L.append(f"**Base case:** {scenario_base}")
    L.append(f"**Bull case:** {scenario_bull}")
    L.append(f"**Bear case:** {scenario_bear}")
    L.append("")

    # ── Macro Dashboard (expanded) ──
    L.append("## **Macro Dashboard**")
    for line in macro_dashboard:
        L.append(line)
    L.append("")
    L.append("**Macro translation:**")
    for b in macro_translation:
        L.append(f"• {b}")
    L.append("")

    # ── Policy & Regulation ──
    L.append("## **Policy & Regulation**")
    if policy_regulation:
        for s in policy_regulation[:8]:
            L.append(f"- {inline_source(s.headline.strip(), s.url)}")
    else:
        L.append("- No major policy or regulation headlines this week.")
    L.append("")

    # ── Analyst & leading voices ──
    L.append("## **Analyst & leading voices**")
    if analyst_voices:
        for s in analyst_voices[:8]:
            L.append(f"- {inline_source(s.headline.strip(), s.url)}")
    else:
        L.append("- No analyst or leading-voice highlights this week.")
    L.append("")

    L.append("*Digital payment tokens are high-risk; this is informational, not financial advice.*")
    return "\n".join(L)
