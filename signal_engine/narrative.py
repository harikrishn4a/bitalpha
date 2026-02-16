"""Rule-based narrative generator: turns data into the 1-2-3 Digest story format.

Generates three sections:
  1) What's happening?  — price action context, sentiment, key levels
  2) Why?               — macro drivers, catalysts, sentiment divergences
  3) Historical parallels & outlook — F&G history, regime precedents
"""
from __future__ import annotations

from signal_engine.normalize import SignalItem


# ── Historical F&G parallel database (rule-based approximations) ──

_FNG_PARALLELS = {
    (0, 10): (
        "Single-digit F&G is extremely rare — historically seen only during major capitulation events. "
        "Prior instances (Jun 2022 F&G at 6, BTC at $17K; Mar 2020 F&G at 8, BTC at $5K) preceded "
        "strong 3-6 month recoveries of 50-200%."
    ),
    (10, 20): (
        "Extreme Fear in the 10-20 range has historically marked local bottoms. "
        "After the Jul 2022 dip to F&G 12 (BTC ~$19K), price rallied 75% over the following 6 months. "
        "However, bottoms can retest — don't assume a V-recovery."
    ),
    (20, 35): (
        "Fear territory (20-35) often coincides with accumulation zones for longer-term holders. "
        "Historically, spending more than 2 weeks in this range has preceded gradual recoveries, "
        "though the timing is uncertain."
    ),
    (35, 55): (
        "Neutral sentiment suggests the market is digesting prior moves. "
        "Direction from here is usually catalyst-driven rather than sentiment-driven."
    ),
    (55, 75): (
        "Greed territory — historically associated with trend continuation in bull markets "
        "but can also precede pullbacks if no catalyst sustains momentum."
    ),
    (75, 90): (
        "High greed (75-90) has historically preceded corrections of 10-25% within 2-4 weeks. "
        "However, in strong bull trends, greed can sustain for months before a meaningful pullback."
    ),
    (90, 101): (
        "Extreme Greed above 90 is rare and almost always precedes a correction. "
        "The Nov 2021 peak (F&G 84, BTC $69K) and Oct 2024 (F&G 92, BTC near ATH) both saw "
        "sharp pullbacks within weeks."
    ),
}


def _fng_parallel(fng_value: int) -> str:
    for (lo, hi), text in _FNG_PARALLELS.items():
        if lo <= fng_value < hi:
            return text
    return "Sentiment at an unusual level — limited historical precedent."


def _price_action_narrative(
    price_usd: float,
    chg_24h: float | None,
    chg_7d: float | None,
    ath_usd: float | None,
    hist_context: dict,
    fng_value: int,
    fng_class: str,
    regime: str,
) -> str:
    """Generate 'What's happening?' paragraph."""
    parts = []

    # Price level + ATH distance
    if ath_usd and ath_usd > 0:
        pct_ath = (price_usd - ath_usd) / ath_usd * 100
        if pct_ath > -5:
            parts.append(f"BTC is trading near its all-time high at ${price_usd:,.0f}, just {abs(pct_ath):.0f}% below the ATH of ${ath_usd:,.0f}.")
        elif pct_ath > -20:
            parts.append(f"BTC at ${price_usd:,.0f} — down {abs(pct_ath):.0f}% from the ATH of ${ath_usd:,.0f}, still within a normal correction range.")
        else:
            parts.append(f"BTC at ${price_usd:,.0f} — down {abs(pct_ath):.0f}% from the ATH of ${ath_usd:,.0f}. This is deep drawdown territory.")
    else:
        parts.append(f"BTC is trading at ${price_usd:,.0f}.")

    # 7d price move context
    if chg_7d is not None:
        if chg_7d < -10:
            parts.append(f"This week saw a sharp {abs(chg_7d):.1f}% selloff — one of the larger weekly drops in recent months.")
        elif chg_7d < -3:
            parts.append(f"Price is down {abs(chg_7d):.1f}% over the past 7 days, continuing a cautious trend.")
        elif chg_7d > 10:
            parts.append(f"A strong {chg_7d:.1f}% rally this week — aggressive buying or short covering likely at play.")
        elif chg_7d > 3:
            parts.append(f"Up {chg_7d:.1f}% this week, showing building momentum.")
        else:
            parts.append("Price has been relatively flat this week — the market is consolidating.")

    # 90d range context
    h = hist_context
    if h.get("pct_from_90d_high") is not None:
        p90 = h["pct_from_90d_high"]
        if p90 < -20:
            parts.append(f"Sitting {abs(p90):.0f}% below the 90-day high — significant ground lost.")
        elif p90 < -5:
            parts.append(f"Trading {abs(p90):.0f}% below the 90-day high ({h.get('high_90d', 0):,.0f}).")

    # Sentiment
    if fng_value <= 15:
        parts.append(f"Sentiment is at *Extreme Fear* ({fng_value}) — the market is panicking.")
    elif fng_value <= 30:
        parts.append(f"Sentiment is fearful ({fng_value}, {fng_class}) — caution is dominant.")
    elif fng_value >= 80:
        parts.append(f"Sentiment at *Extreme Greed* ({fng_value}) — euphoria is building; historically a warning sign.")
    elif fng_value >= 60:
        parts.append(f"Sentiment leaning greedy ({fng_value}, {fng_class}) — confidence is elevated.")

    return " ".join(parts)


def _why_narrative(
    regime: str,
    macro_translation: list[str],
    catalysts: list[SignalItem],
    fng_value: int,
    chg_7d: float | None,
    global_crypto: dict | None = None,
) -> list[str]:
    """Generate 'Why?' bullets."""
    bullets = []

    # Macro drivers
    for mt in macro_translation:
        if mt and "unavailable" not in mt.lower() and "add fred" not in mt.lower():
            bullets.append(mt)

    # Catalyst-specific
    for c in catalysts[:3]:
        hl = c.headline.lower()
        if any(kw in hl for kw in ("fomc", "fed", "rate", "cpi", "inflation", "nfp", "payroll")):
            bullets.append(f"Key catalyst: {c.headline}" + (f" [[Source]]({c.url})" if c.url else ""))

    # Sentiment divergence detection
    if fng_value < 25 and chg_7d is not None and chg_7d > 0:
        bullets.append("Sentiment divergence: F&G shows extreme fear, but price is actually up this week — sellers may be exhausted.")
    elif fng_value > 70 and chg_7d is not None and chg_7d < -2:
        bullets.append("Sentiment divergence: F&G shows greed, but price is falling — hidden distribution, be cautious.")

    # Crypto market breadth
    if global_crypto:
        dom = global_crypto.get("market_cap_percentage", {}).get("btc")
        if dom is not None:
            if dom > 55:
                bullets.append(f"BTC dominance at {dom:.1f}% — capital rotating into BTC from alts (risk-off within crypto).")
            elif dom < 40:
                bullets.append(f"BTC dominance at {dom:.1f}% — capital flowing to alts (risk-on within crypto).")

    # Regime context
    if regime == "Breakdown":
        bullets.append("Regime: Breakdown — price below key moving averages with accelerating selling pressure.")
    elif regime == "Squeeze":
        bullets.append("Regime: Squeeze — volatility compressing; expect a large move soon (direction unclear).")
    elif regime == "Risk-off":
        bullets.append("Regime: Risk-off — flight to safety in traditional markets is spilling over to crypto.")

    if not bullets:
        bullets.append(f"Market in {regime} mode — no single dominant driver; watching for catalysts to break the deadlock.")

    return bullets


def _outlook_narrative(
    regime: str,
    fng_value: int,
    levels: dict,
    chg_7d: float | None,
) -> str:
    """Generate 'Historical parallels & outlook' paragraph."""
    parts = []

    # F&G historical parallel
    parts.append(_fng_parallel(fng_value))

    # Regime-based outlook
    s1 = levels.get("S1", 0)
    r1 = levels.get("R1", 0)
    if regime == "Breakdown":
        parts.append(
            f"In Breakdown regimes, the key question is whether S1 ({s1:,.0f}) holds. "
            f"If it does on high volume, that's a potential reversal. If it breaks, expect acceleration toward S2."
        )
    elif regime == "Chop":
        parts.append(
            f"Expect choppy price action between {s1:,.0f} and {r1:,.0f}. "
            f"A decisive breakout with volume from this range will set the next trend."
        )
    elif regime == "Trend":
        parts.append(
            f"Trend regimes tend to persist longer than most expect. "
            f"Pullbacks to the Pivot level are buying opportunities as long as the trend structure holds."
        )
    elif regime == "Risk-on":
        parts.append(
            f"Risk-on conditions favour crypto. Watch for continuation toward R1 ({r1:,.0f}). "
            f"The risk is a sudden macro shock that flips sentiment."
        )
    elif regime == "Squeeze":
        parts.append(
            "Squeeze regimes resolve violently. Position sizing matters more than direction here — "
            "keep exposure light and let the breakout show you the way."
        )
    else:
        parts.append(
            f"Current regime ({regime}) suggests watching the {s1:,.0f}-{r1:,.0f} range for resolution."
        )

    return " ".join(parts)


def generate_digest(
    *,
    price_usd: float,
    chg_24h: float | None,
    chg_7d: float | None,
    ath_usd: float | None,
    hist_context: dict,
    fng_value: int,
    fng_class: str,
    regime: str,
    levels: dict,
    macro_translation: list[str],
    catalysts: list[SignalItem],
    global_crypto: dict | None = None,
) -> dict:
    """Generate the 1-2-3 Digest narrative.

    Returns:
        {"whats_happening": str, "why": list[str], "outlook": str}
    """
    return {
        "whats_happening": _price_action_narrative(
            price_usd, chg_24h, chg_7d, ath_usd, hist_context, fng_value, fng_class, regime,
        ),
        "why": _why_narrative(
            regime, macro_translation, catalysts, fng_value, chg_7d, global_crypto,
        ),
        "outlook": _outlook_narrative(regime, fng_value, levels, chg_7d),
    }
