"""Chart gating: decide whether a chart is significant enough to include."""
from __future__ import annotations

NO_CHART_MSG = "No chart today — nothing materially changed in structure/flows/volatility."

# Chart types the system can produce (open-ended)
CHART_TYPES = [
    "btc_price_ma",            # BTC price + moving averages
    "btc_vs_dxy",              # BTC vs Dollar index overlay
    "btc_vs_yields",           # BTC vs 10Y yields
    "btc_vs_spx",              # BTC vs S&P 500
    "volatility_atr",          # ATR / realized vol
    "fear_greed_vs_price",     # F&G vs BTC price
    "dominance",               # BTC dominance chart
    "fintech_relative",        # Fintech sector relative strength
]


def _vol_score(market_data: dict) -> int:
    """Score based on volatility change. 0-25."""
    chg_24h = abs(market_data.get("chg_24h", 0) or 0)
    chg_7d = abs(market_data.get("chg_7d", 0) or 0)
    s = 0
    if chg_24h > 5:
        s += 15
    elif chg_24h > 3:
        s += 10
    elif chg_24h > 1.5:
        s += 5
    if chg_7d > 10:
        s += 10
    elif chg_7d > 5:
        s += 7
    elif chg_7d > 2:
        s += 3
    return min(25, s)


def _regime_shift_score(current_regime: str, prev_regime: str | None) -> int:
    """Score based on regime change. 0-30."""
    if not prev_regime:
        return 10
    if current_regime != prev_regime:
        return 30
    return 0


def _fng_extreme_score(fng_value: int) -> int:
    """Score based on F&G extremes. 0-20."""
    if fng_value <= 10 or fng_value >= 90:
        return 20
    if fng_value <= 20 or fng_value >= 80:
        return 12
    if fng_value <= 30 or fng_value >= 70:
        return 6
    return 0


def _catalyst_score(upcoming_events: int) -> int:
    """Score based on catalyst density. 0-25."""
    if upcoming_events >= 3:
        return 25
    if upcoming_events >= 2:
        return 18
    if upcoming_events >= 1:
        return 10
    return 0


def chart_significance_score(
    market_data: dict,
    current_regime: str,
    prev_regime: str | None,
    fng_value: int,
    upcoming_events_count: int,
) -> int:
    """Compute ChartSignificanceScore (0-100)."""
    return min(100, (
        _vol_score(market_data)
        + _regime_shift_score(current_regime, prev_regime)
        + _fng_extreme_score(fng_value)
        + _catalyst_score(upcoming_events_count)
    ))


def select_chart_type(
    market_data: dict,
    current_regime: str,
    prev_regime: str | None,
) -> str:
    """Pick the best chart type for today based on what changed."""
    regime_shifted = prev_regime and current_regime != prev_regime
    chg_24h = abs(market_data.get("chg_24h", 0) or 0)

    if regime_shifted:
        return "btc_price_ma"
    if chg_24h > 5:
        return "volatility_atr"
    # Default: price + MAs
    return "btc_price_ma"


def gate(
    market_data: dict,
    current_regime: str,
    prev_regime: str | None,
    fng_value: int,
    upcoming_events_count: int,
    threshold: int = 70,
) -> tuple[bool, int, str]:
    """Run the chart gate. Returns (show_chart, score, chart_type_or_no_chart_msg)."""
    score = chart_significance_score(
        market_data, current_regime, prev_regime, fng_value, upcoming_events_count
    )
    if score >= threshold:
        chart_type = select_chart_type(market_data, current_regime, prev_regime)
        return True, score, chart_type
    return False, score, NO_CHART_MSG
