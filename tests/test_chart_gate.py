"""Unit tests for chart gating."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signal_engine.chart_gate import (
    chart_significance_score, gate, select_chart_type, NO_CHART_MSG,
)


def test_score_range():
    s = chart_significance_score(
        market_data={"chg_24h": 1, "chg_7d": 2},
        current_regime="Chop", prev_regime="Chop",
        fng_value=50, upcoming_events_count=0,
    )
    assert 0 <= s <= 100


def test_high_vol_boosts_score():
    low = chart_significance_score(
        {"chg_24h": 0.5, "chg_7d": 1}, "Chop", "Chop", 50, 0)
    high = chart_significance_score(
        {"chg_24h": 8, "chg_7d": 15}, "Chop", "Chop", 50, 0)
    assert high > low


def test_regime_shift_boosts_score():
    stable = chart_significance_score(
        {"chg_24h": 1}, "Trend", "Trend", 50, 0)
    shifted = chart_significance_score(
        {"chg_24h": 1}, "Breakdown", "Trend", 50, 0)
    assert shifted > stable


def test_fng_extreme_boosts_score():
    normal = chart_significance_score(
        {"chg_24h": 1}, "Chop", "Chop", 50, 0)
    extreme = chart_significance_score(
        {"chg_24h": 1}, "Chop", "Chop", 5, 0)
    assert extreme > normal


def test_gate_below_threshold():
    show, score, msg = gate(
        {"chg_24h": 0.1, "chg_7d": 0.2},
        "Chop", "Chop", 50, 0, threshold=70,
    )
    assert not show
    assert msg == NO_CHART_MSG


def test_gate_above_threshold():
    show, score, chart_type = gate(
        {"chg_24h": 8, "chg_7d": 12},
        "Breakdown", "Trend", 10, 3, threshold=70,
    )
    assert show
    assert chart_type in ("btc_price_ma", "volatility_atr")


def test_select_chart_type_regime_shift():
    t = select_chart_type({"chg_24h": 1}, "Breakdown", "Trend")
    assert t == "btc_price_ma"


def test_select_chart_type_high_vol():
    t = select_chart_type({"chg_24h": 7}, "Chop", "Chop")
    assert t == "volatility_atr"


if __name__ == "__main__":
    test_score_range()
    test_high_vol_boosts_score()
    test_regime_shift_boosts_score()
    test_fng_extreme_boosts_score()
    test_gate_below_threshold()
    test_gate_above_threshold()
    test_select_chart_type_regime_shift()
    test_select_chart_type_high_vol()
    print("All chart gate tests passed!")
