"""Macro metrics from FRED. Format for digest display."""
from ..apis import fred as fred_api


def format_macro(fred_data: dict | None) -> list[str]:
    """Format FRED series for Macro Dashboard. Returns list of lines."""
    if not fred_data:
        return ["(macro data unavailable — add FRED_API_KEY)"]
    lines = []
    labels = {
        "DGS10": "10Y yield",
        "DTWEXBGS": "Dollar index",
        "T10Y2Y": "10-2 spread",
        "ICSA": "Initial claims",
        "CPIAUCSL": "CPI",
        "FEDFUNDS": "Fed funds",
    }
    for sid, label in labels.items():
        obs = fred_data.get(sid, [])
        if not obs:
            continue
        latest = next((o for o in obs if o.get("value") not in (".", None, "")), None)
        prev = next((o for o in obs[1:] if o.get("value") not in (".", None, "")), None)
        if not latest:
            continue
        val = latest.get("value", "")
        line = f"- {label}: {val}"
        if prev and sid in ("DGS10", "DTWEXBGS", "ICSA"):
            try:
                v0 = float(prev["value"])
                v1 = float(val)
                chg = v1 - v0
                line += f" (WoW {chg:+.2f})"
            except (ValueError, TypeError):
                pass
        lines.append(line)
    return lines if lines else ["(macro data unavailable)"]


def macro_translation(fred_data: dict | None) -> list[str]:
    """3 bullet macro translation lines."""
    bullets = []
    if not fred_data:
        return ["Add FRED_API_KEY for macro translation."]
    # DGS10
    dgs = fred_data.get("DGS10", [])
    dgs_latest = next((float(o["value"]) for o in dgs if o.get("value") not in (".", None, "")), None)
    dgs_prev = next((float(o["value"]) for o in dgs[1:] if o.get("value") not in (".", None, "")), None) if len(dgs) > 1 else None
    if dgs_latest is not None and dgs_prev is not None and dgs_latest - dgs_prev > 0.2:
        bullets.append("Yields up strongly → risk assets headwind")
    # DTWEXBGS
    dtwex = fred_data.get("DTWEXBGS", [])
    dtwex_latest = next((float(o["value"]) for o in dtwex if o.get("value") not in (".", None, "")), None)
    dtwex_prev = next((float(o["value"]) for o in dtwex[1:] if o.get("value") not in (".", None, "")), None) if len(dtwex) > 1 else None
    if dtwex_latest is not None and dtwex_prev is not None and dtwex_latest - dtwex_prev > 0.5:
        bullets.append("Dollar up strongly → risk assets headwind")
    # ICSA + DGS10: claims rising + yields falling
    icsa = fred_data.get("ICSA", [])
    icsa_latest = next((float(o["value"]) for o in icsa if o.get("value") not in (".", None, "")), None)
    icsa_prev = next((float(o["value"]) for o in icsa[1:] if o.get("value") not in (".", None, "")), None) if len(icsa) > 1 else None
    if icsa_latest and icsa_prev and icsa_latest > icsa_prev and dgs_latest and dgs_prev and dgs_latest < dgs_prev:
        bullets.append("Claims rising + yields falling → rate-cut expectations")
    if not bullets:
        bullets.append("No strong macro signals this week.")
    return bullets[:3]
