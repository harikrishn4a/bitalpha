"""Unit tests for signal scoring determinism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signal_engine.normalize import SignalItem
from signal_engine.scoring import score, score_batch


def _make_item(**kwargs) -> SignalItem:
    defaults = {
        "id": "test1", "source": "coingecko", "category": "crypto_catalyst",
        "headline": "BTC $100,000", "body": "", "url": "https://example.com",
        "timestamp": "2026-02-15T00:00:00",
    }
    defaults.update(kwargs)
    return SignalItem(**defaults)


def test_score_range():
    """Score must always be 0-100."""
    item = _make_item()
    scored = score(item)
    assert 0 <= scored.signal_score <= 100, f"Score out of range: {scored.signal_score}"


def test_score_deterministic():
    """Same input must produce same score."""
    a = score(_make_item())
    b = score(_make_item())
    assert a.signal_score == b.signal_score


def test_fred_higher_credibility():
    """FRED source should score higher credibility than x_trends."""
    fred = score(_make_item(source="fred", category="macro"))
    x = score(_make_item(source="x_trends", category="social"))
    assert fred.credibility > x.credibility


def test_score_components_add_up():
    """signal_score = price_impact + novelty + credibility + time_sensitivity."""
    item = score(_make_item())
    expected = item.price_impact + item.novelty + item.credibility + item.time_sensitivity
    assert item.signal_score == expected


def test_why_you_got_this():
    """Must produce exactly 2 'why' bullets."""
    item = score(_make_item())
    assert len(item.why_you_got_this) == 2


def test_score_batch_sorted():
    """score_batch returns items sorted by score descending."""
    items = [
        _make_item(id="a", source="x_trends", category="social"),
        _make_item(id="b", source="fred", category="macro"),
    ]
    scored = score_batch(items)
    assert scored[0].signal_score >= scored[1].signal_score


def test_fng_extreme_boosts_score():
    """F&G extreme values should boost price_impact."""
    normal = score(_make_item(raw_data={"fng_value": 50}))
    extreme = score(_make_item(raw_data={"fng_value": 5}))
    assert extreme.price_impact >= normal.price_impact


if __name__ == "__main__":
    test_score_range()
    test_score_deterministic()
    test_fred_higher_credibility()
    test_score_components_add_up()
    test_why_you_got_this()
    test_score_batch_sorted()
    test_fng_extreme_boosts_score()
    print("All scoring tests passed!")
