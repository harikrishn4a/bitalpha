"""Narrative blocks: Learn 1 Thing, safety tip, MAS disclaimer."""
from datetime import datetime

LEARN_ONE_THING = [
    ("What moves BTC? liquidity vs narratives", "Like a boat on tides: liquidity is the water, narratives are the wind.", "Misconception: Only fundamentals matter — liquidity often leads."),
    ("What is a moving average and why it matters", "It smooths noise like a rolling average of your last N steps.", "Misconception: MA predicts the future — it lags price."),
    ("What is real yield and why crypto cares", "Real yield = nominal yield minus inflation; when it rises, risk assets often fall.", "Misconception: Higher yields are always bad — it depends on why."),
    ("What is the dollar index and why it correlates", "DXY measures USD vs basket of currencies; when USD strengthens, risk assets often weaken.", "Misconception: DXY and BTC always move opposite — correlation isn't perfect."),
    ("What are stablecoins and why fintech uses them", "Stablecoins peg to fiat; used for fast settlement and yield.", "Misconception: All stablecoins are equally safe — counterparty risk varies."),
    ("Payment rails: Visa/FAST/SWIFT vs crypto settlement", "Traditional rails are batch and slow; crypto can settle in minutes.", "Misconception: Crypto always settles faster — congestion can delay."),
    ("Custody and counterparty risk", "Not your keys, not your coins — exchanges hold your keys unless self-custody.", "Big exchanges can't fail — history says otherwise."),
    ("Leverage, liquidations, and volatility", "Leverage amplifies gains and losses; liquidations cascade in volatile moves.", "Misconception: Leverage is always bad — it's a tool, use wisely."),
]

SAFETY_TIPS = [
    "Seed phrase: Write it down, never store digitally.",
    "Fake support: Official teams never DM first.",
    "2FA: Use an app (Google Authenticator), not SMS.",
    "Passkeys: Prefer passkeys over passwords where supported.",
    "Test transaction: Send a small amount first.",
]

MAS_DISCLAIMER = "Digital payment tokens are high-risk; this is informational, not financial advice."


def learn_one_thing(week_of_year: int | None = None) -> tuple[str, str, str]:
    """Return (title, analogy, misconception) for the week. Deterministic via week number."""
    w = week_of_year if week_of_year is not None else datetime.now().isocalendar()[1]
    idx = (w - 1) % 8
    return LEARN_ONE_THING[idx]


def safety_tip(day_of_year: int | None = None) -> str:
    """Rotate safety tip by day."""
    d = day_of_year if day_of_year is not None else datetime.now().timetuple().tm_yday
    return SAFETY_TIPS[d % len(SAFETY_TIPS)]


def mas_disclaimer() -> str:
    return MAS_DISCLAIMER
