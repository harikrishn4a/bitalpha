"""Daily 'If this, then that' playbook generator."""
from __future__ import annotations

from .normalize import SignalItem


def generate_playbook(regime: str, catalysts: list[SignalItem],
                      fng_value: int, market_data: dict) -> str:
    """Generate one short 'if this, then that' rule tied to today's catalysts + regime."""
    chg_24h = market_data.get("chg_24h", 0) or 0

    # Catalyst-driven rules
    for c in catalysts:
        hl = c.headline.lower()
        if "fomc" in hl or "fed" in hl:
            return (
                "If FOMC signals hawkish surprise (higher dots, taper talk) → expect BTC to test "
                "support levels within 24h. If dovish → look for relief rally toward R1."
            )
        if "cpi" in hl or "inflation" in hl:
            return (
                "If CPI comes in hot (above consensus) → yields spike, BTC likely sells off to S1. "
                "If cool → rate-cut bets rise, BTC bounces."
            )
        if "nfp" in hl or "payroll" in hl or "jobs" in hl:
            return (
                "If NFP surprises strong → USD strengthens, BTC faces headwind. "
                "If weak → recession fears but rate-cut hopes; BTC direction depends on regime."
            )

    # Regime-driven fallback
    if regime == "Breakdown" and fng_value < 20:
        return (
            "If BTC holds S1 on high volume → potential reversal setup. "
            "If S1 breaks → next target is S2; reduce exposure."
        )
    if regime == "Squeeze":
        return (
            "If BTC breaks above R1 with volume → momentum entry. "
            "If rejects → stay flat; squeeze can resolve in either direction."
        )
    if regime == "Trend" and chg_24h > 0:
        return (
            "If BTC stays above Pivot on pullback → trend intact, add on dips. "
            "If Pivot breaks → trend may be exhausting; tighten stops."
        )
    if regime == "Risk-off":
        return (
            "If USD continues strengthening → BTC likely drifts lower; wait for reversal. "
            "If risk-off eases (yields drop) → watch for mean-reversion bounce."
        )
    if regime == "Risk-on":
        return (
            "If macro stays supportive (yields flat, USD soft) → BTC likely grinds higher. "
            "If sudden risk event → take partial profits near R1."
        )
    # Chop default
    return (
        "If BTC stays between S1 and R1 → range-trade; buy near S1, take profit near R1. "
        "If breaks out of range with volume → follow the breakout direction."
    )
