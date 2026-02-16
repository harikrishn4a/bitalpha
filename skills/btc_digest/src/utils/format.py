"""Format helpers for digest output."""


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
