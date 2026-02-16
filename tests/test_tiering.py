"""Unit tests for tier classification."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signal_engine.normalize import SignalItem
from signal_engine.tiering import classify, classify_batch, filter_by_tier


def _make_item(score: int) -> SignalItem:
    item = SignalItem(
        id=f"t{score}", source="test", category="macro",
        headline="Test", body="", url="", timestamp="2026-02-15T00:00:00",
    )
    item.signal_score = score
    return item


def test_fyi_tier():
    item = classify(_make_item(30))
    assert item.tier == "FYI"


def test_heads_up_tier():
    item = classify(_make_item(65))
    assert item.tier == "Heads Up"


def test_actionable_tier():
    item = classify(_make_item(85))
    assert item.tier == "Actionable"


def test_boundary_fyi_to_heads_up():
    fyi = classify(_make_item(59))
    heads = classify(_make_item(60))
    assert fyi.tier == "FYI"
    assert heads.tier == "Heads Up"


def test_boundary_heads_to_actionable():
    heads = classify(_make_item(79))
    action = classify(_make_item(80))
    assert heads.tier == "Heads Up"
    assert action.tier == "Actionable"


def test_classify_batch():
    items = [_make_item(30), _make_item(70), _make_item(90)]
    classified = classify_batch(items)
    assert [c.tier for c in classified] == ["FYI", "Heads Up", "Actionable"]


def test_filter_by_tier():
    items = [_make_item(30), _make_item(70), _make_item(90)]
    classified = classify_batch(items)
    hot = filter_by_tier(classified, min_tier="Heads Up")
    assert len(hot) == 2
    assert all(h.tier in ("Heads Up", "Actionable") for h in hot)


def test_filter_actionable_only():
    items = classify_batch([_make_item(30), _make_item(70), _make_item(90)])
    action = filter_by_tier(items, min_tier="Actionable")
    assert len(action) == 1
    assert action[0].tier == "Actionable"


if __name__ == "__main__":
    test_fyi_tier()
    test_heads_up_tier()
    test_actionable_tier()
    test_boundary_fyi_to_heads_up()
    test_boundary_heads_to_actionable()
    test_classify_batch()
    test_filter_by_tier()
    test_filter_actionable_only()
    print("All tiering tests passed!")
