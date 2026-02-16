"""Formatting helpers for numbers, prices, and inline sources."""
from __future__ import annotations


def fmt_num(x, decimals: int = 0) -> str:
    """Format number with commas. e.g. 69094 -> '69,094'."""
    if x is None:
        return "N/A"
    try:
        n = float(x)
        if decimals == 0:
            return f"{int(round(n)):,}"
        return f"{n:,.{decimals}f}"
    except (TypeError, ValueError):
        return str(x)


def fmt_price(x) -> str:
    """Format price with commas, no decimals for whole numbers."""
    if x is None:
        return "N/A"
    try:
        n = float(x)
        if n >= 1000:
            return f"{int(round(n)):,}"
        return f"{n:,.2f}"
    except (TypeError, ValueError):
        return str(x)


def fmt_pct(x, sign: bool = True) -> str:
    """Format percentage. e.g. -2.89 -> '-2.9%'."""
    if x is None:
        return "N/A"
    try:
        n = float(x)
        return f"{n:+.1f}%" if sign else f"{n:.1f}%"
    except (TypeError, ValueError):
        return str(x)


def inline_source(text: str, url: str | None) -> str:
    """Attach an inline source link beside a claim. Returns 'text [Source](url)' or just 'text'."""
    if not url:
        return text
    return f"{text} [[Source]]({url})"
