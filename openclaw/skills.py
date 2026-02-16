"""OpenClaw skill entry points: run_weekly, run_daily, run_hourly, send_alert."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

# Ensure project root is on sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env")

import yaml
from storage.cache import FileCache
from storage.db import SignalDB
from data_sources.fred import FredSource
from data_sources.coingecko import CoinGeckoSource
from data_sources.coinmarketcal import CoinMarketCalSource
from data_sources.newsapi import NewsAPISource
from data_sources.gdelt import GDELTSource
from data_sources.x_trends import XTrendsSource
from data_sources.finnhub import FinnhubSource
from signal_engine.normalize import normalize_raw, SignalItem
from signal_engine.dedupe import dedupe
from signal_engine.scoring import score_batch
from signal_engine.tiering import classify_batch, filter_by_tier
from signal_engine import regime as regime_mod
from signal_engine import macro_analysis
from signal_engine import chart_gate
from signal_engine import playbook as playbook_mod
from signal_engine import narrative as narrative_mod
from outputs import weekly_renderer, daily_renderer, hourly_renderer, charts
from openclaw.dispatch import send_alert as _send

# ── Config ──

def _load_config() -> dict:
    cfg_path = _ROOT / "config.yaml"
    if cfg_path.exists():
        with open(cfg_path) as f:
            return yaml.safe_load(f) or {}
    return {}

CFG = _load_config()

import os
_CACHE_DIR = os.getenv("CACHE_DIR", str(_ROOT / ".cache"))
_DB_PATH = os.getenv("DB_PATH", str(_ROOT / "storage" / "signals.db"))
_CHART_DIR = Path(os.getenv("CHART_DIR", str(Path.home() / ".openclaw" / "workspace")))
_TZ = os.getenv("TIMEZONE", "Asia/Singapore")

cache = FileCache(_CACHE_DIR, ttl=CFG.get("cache", {}).get("ttl_seconds", 300))
db = SignalDB(_DB_PATH)


# ── Narrative content (reused from old system) ──

_LEARN = [
    ("What moves BTC? Liquidity vs narratives", "Like a boat on tides: liquidity is the water, narratives are the wind.", "Only fundamentals matter — liquidity often leads."),
    ("What is a moving average and why it matters", "It smooths noise like a rolling average of your last N steps.", "MA predicts the future — it lags price."),
    ("What is real yield and why crypto cares", "Real yield = nominal yield minus inflation; when it rises, risk assets often fall.", "Higher yields are always bad — it depends on why."),
    ("What is DXY and why it correlates", "DXY measures USD vs a basket; when USD strengthens, risk assets often weaken.", "DXY and BTC always move opposite — correlation isn't perfect."),
    ("What are stablecoins and why fintech uses them", "Stablecoins peg to fiat; used for fast settlement and yield.", "All stablecoins are equally safe — counterparty risk varies."),
    ("Custody and counterparty risk", "Not your keys, not your coins — exchanges hold your keys unless self-custody.", "Big exchanges can't fail — history says otherwise."),
    ("Leverage, liquidations, and volatility", "Leverage amplifies gains and losses; liquidations cascade in volatile moves.", "Leverage is always bad — it's a tool, use wisely."),
    ("Payment rails: SWIFT vs crypto settlement", "Traditional rails are batch and slow; crypto can settle in minutes.", "Crypto always settles faster — congestion can delay."),
]

_SAFETY_TIPS = [
    "Seed phrase: Write it down, never store digitally.",
    "Fake support: Official teams never DM first.",
    "2FA: Use an app (Google Authenticator), not SMS.",
    "Passkeys: Prefer passkeys over passwords where supported.",
    "Test transaction: Send a small amount first.",
]


def _now():
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(_TZ)
        return datetime.now(tz)
    except ImportError:
        return datetime.now()


# ── Source collection ──

def _news_filter_keywords() -> list[str]:
    """Merge config news_keywords.crypto + .fintech for client-side relevance filtering."""
    kw = CFG.get("news_keywords", {})
    return list(kw.get("crypto", [])) + list(kw.get("fintech", []))


def _collect_all_sources() -> list[dict]:
    """Fetch from all configured sources. Returns raw signal dicts."""
    raw = []
    filter_kw = _news_filter_keywords()
    sources = [
        FredSource(cache),
        CoinGeckoSource(cache),
        CoinMarketCalSource(cache),
        FinnhubSource(cache),
    ]
    # News source toggle; filter so only crypto/fintech-relevant articles pass
    ns = CFG.get("news_source", "newsapi")
    if ns == "newsapi":
        sources.append(NewsAPISource(cache, filter_keywords=filter_kw))
    else:
        sources.append(GDELTSource(cache, filter_keywords=filter_kw))
    sources.append(XTrendsSource(cache))

    for src in sources:
        try:
            raw.extend(src.fetch_signals())
        except Exception as e:
            print(f"[WARN] {src.name} failed: {e}", file=sys.stderr)
    return raw


def _collect_fast_sources() -> list[dict]:
    """Fetch fast-updating sources for hourly news brief."""
    raw = []
    filter_kw = _news_filter_keywords()
    ns = CFG.get("news_source", "newsapi")
    news_src = NewsAPISource(cache, filter_keywords=filter_kw) if ns == "newsapi" else GDELTSource(cache, filter_keywords=filter_kw)
    for src in [CoinGeckoSource(cache), XTrendsSource(cache), FinnhubSource(cache), news_src]:
        try:
            raw.extend(src.fetch_signals())
        except Exception as e:
            print(f"[WARN] {src.name} failed: {e}", file=sys.stderr)
    return raw


def _pipeline(raw: list[dict]) -> list[SignalItem]:
    """Normalize -> dedupe -> score -> classify."""
    items = normalize_raw(raw)
    seen = db.recent_signal_ids(hours=CFG.get("cache", {}).get("dedup_window_hours", 48))
    items = dedupe(items, seen)
    items = score_batch(items)
    items = classify_batch(items)
    # Persist
    for item in items:
        db.upsert_signal(item.to_dict())
    return items


# ── Market data helpers ──

def _get_market_data() -> dict:
    cg = CoinGeckoSource(cache)
    try:
        detail = cg.coin_detail()
    except Exception as e:
        print(f"[WARN] CoinGecko coin_detail failed: {e}", file=sys.stderr)
        detail = {}
    md = detail.get("market_data", {})
    return {
        "price_usd": md.get("current_price", {}).get("usd"),
        "price_sgd": md.get("current_price", {}).get("sgd"),
        "chg_24h": md.get("price_change_percentage_24h"),
        "chg_7d": md.get("price_change_percentage_7d"),
        "chg_ytd": md.get("price_change_percentage_200d"),  # approx
        "ath_usd": md.get("ath", {}).get("usd"),
    }


def _get_fng() -> tuple[int, str, str]:
    cg = CoinGeckoSource(cache)
    try:
        fng = cg.fear_greed_latest().get("data", [{}])
    except Exception:
        fng = [{}]
    val = int(fng[0].get("value", 50)) if fng else 50
    cls = fng[0].get("value_classification", "Neutral") if fng else "Neutral"
    try:
        hist = cg.fear_greed_history(30).get("data", [])
    except Exception:
        hist = []
    vals = [int(d["value"]) for d in hist if d.get("value")]
    rng = f"{min(vals)}–{max(vals)}" if vals else "N/A"
    return val, cls, rng


# ══════════════════════════════════════════════════
#  PUBLIC SKILL ENTRY POINTS
# ══════════════════════════════════════════════════

def run_weekly_update(print_only: bool = False):
    """Generate and send the weekly macro update."""
    now = _now()
    date_str = now.strftime("%a %d %b %Y, %H:%M SGT")

    # Collect & process signals
    raw = _collect_all_sources()
    items = _pipeline(raw)

    # Market data
    mdata = _get_market_data()
    fng_val, fng_cls, fng_rng = _get_fng()

    # Regime
    cg = CoinGeckoSource(cache)
    try:
        mkt_chart = cg.market_chart(days=90)
    except Exception as e:
        print(f"[WARN] CoinGecko market_chart failed: {e}", file=sys.stderr)
        mkt_chart = {"prices": []}
    df = regime_mod.prices_df(mkt_chart)
    fred = FredSource(cache)
    try:
        fred_data = fred.fetch_all_series()
    except Exception as e:
        print(f"[WARN] FRED fetch failed: {e}", file=sys.stderr)
        fred_data = {}
    drivers = macro_analysis.extract_drivers(fred_data)
    dxy_chg = None
    dxy_obs = fred_data.get("DTWEXBGS", [])
    if len(dxy_obs) >= 2:
        try:
            dxy_chg = float(dxy_obs[0]["value"]) - float(dxy_obs[1]["value"])
        except (ValueError, KeyError):
            pass
    current_regime = regime_mod.detect_regime(df, fng_val, dxy_chg)
    levels = regime_mod.compute_levels(df, mdata.get("price_usd", 0) or 0)
    hist = regime_mod.historic_context(df, mdata.get("ath_usd"))
    prev = db.latest_regime()
    delta = regime_mod.compute_delta(
        {"regime_tag": current_regime, "drivers": drivers},
        prev,
    )
    db.save_regime(now.strftime("%Y-%m-%d"), current_regime, drivers, delta)

    # Catalysts
    catalysts = [i for i in items if i.category in ("macro", "crypto_catalyst") and i.source in ("fred", "coinmarketcal")]

    # Fintech: separate quotes (movers) from news (catalysts)
    fintech_quote_items = [
        i for i in items
        if i.category == "fintech" and i.raw_data.get("is_quote")
    ]
    fintech_news_items = [
        i for i in items
        if i.category == "fintech" and not i.raw_data.get("is_quote")
    ]

    # Build movers list sorted by absolute % change
    fintech_movers = []
    for fq in fintech_quote_items:
        sym = fq.raw_data.get("symbol", "")
        chg = fq.raw_data.get("dp", 0) or 0
        price_val = fq.raw_data.get("c", 0) or 0
        # Find a news catalyst for this symbol, if any
        catalyst = None
        for fn in fintech_news_items:
            if fn.raw_data.get("symbol") == sym:
                catalyst = fn.headline.replace(f"[{sym}] ", "")
                break
        fintech_movers.append({
            "symbol": sym,
            "price": price_val,
            "chg_pct": chg,
            "catalyst": catalyst,
        })
    fintech_movers.sort(key=lambda x: abs(x["chg_pct"]), reverse=True)

    # Global crypto market data (dominance, volume)
    try:
        global_crypto = cg.global_data()
    except Exception:
        global_crypto = {}

    # Macro dashboard (includes crypto breadth from CoinGecko)
    macro_dash = macro_analysis.format_dashboard(fred_data, global_crypto)
    macro_trans = macro_analysis.macro_translation(fred_data)

    # Narrative digest (the 1-2-3 story)
    price = mdata.get("price_usd", 0) or 0
    digest = narrative_mod.generate_digest(
        price_usd=price,
        chg_24h=mdata.get("chg_24h"),
        chg_7d=mdata.get("chg_7d"),
        ath_usd=mdata.get("ath_usd"),
        hist_context=hist,
        fng_value=fng_val,
        fng_class=fng_cls,
        regime=current_regime,
        levels=levels,
        macro_translation=macro_trans,
        catalysts=catalysts,
        global_crypto=global_crypto,
    )

    # Scenario (rule-based)
    scenario_base = f"BTC consolidates around ${price:,.0f}; regime stays {current_regime}. Watch macro data for direction."
    scenario_bull = f"If macro eases (yields drop, USD softens) → BTC pushes toward R1 ({levels.get('R1', 0):,.0f}). Catalyst: dovish FOMC or cool CPI."
    scenario_bear = f"If macro tightens (yields spike, USD rallies) → BTC tests S1 ({levels.get('S1', 0):,.0f}). Risk: hot inflation print or hawkish surprise."

    # Learn
    w = now.isocalendar()[1]
    learn = _LEARN[(w - 1) % len(_LEARN)]
    text = weekly_renderer.render(
        date_str=date_str,
        digest=digest,
        catalysts=catalysts,
        price_usd=price, price_sgd=mdata.get("price_sgd"),
        chg_7d=mdata.get("chg_7d"), chg_ytd=mdata.get("chg_ytd"),
        ath_usd=mdata.get("ath_usd"),
        fng_value=fng_val, fng_class=fng_cls, fng_30d_range=fng_rng,
        levels=levels, regime=current_regime, hist_context=hist,
        scenario_base=scenario_base, scenario_bull=scenario_bull, scenario_bear=scenario_bear,
        fintech_movers=fintech_movers,
        fintech_news=fintech_news_items,
        exchange_signals=[i for i in items if "exchange" in i.headline.lower()],
        macro_dashboard=macro_dash,
        macro_translation=macro_trans,
        macro_delta=delta,
        regime_drivers=drivers,
        learn_title=learn[0], learn_body=learn[1], learn_misconception=learn[2],
    )

    # Chart
    chart_path = None
    try:
        chart_path = str(charts.generate_btc_price_ma(mkt_chart, _CHART_DIR / "weekly_chart.png"))
    except Exception:
        pass

    if print_only:
        print(text)
        if chart_path:
            print(f"\n[Chart: {chart_path}]")
    else:
        _send(text, chart_path)


def run_daily_update(print_only: bool = False):
    """Generate and send the daily update — BTC price + news roundup."""
    now = _now()
    date_str = now.strftime("%a %d %b %Y, %H:%M SGT")

    # Collect all signals
    raw = _collect_all_sources()
    items = _pipeline(raw)
    mdata = _get_market_data()
    fng_val, fng_cls, _ = _get_fng()
    price = mdata.get("price_usd", 0) or 0

    # Separate signals by category
    crypto_news = [i for i in items if i.category in ("crypto_catalyst", "macro")]
    fintech_signals = [i for i in items if i.category == "fintech"]
    social_signals = [i for i in items if i.category == "social"]

    # Split fintech into quotes vs news
    fintech_news = [i for i in fintech_signals if not (i.raw_data or {}).get("is_quote")]
    # Get fintech movers from Finnhub directly
    fh = FinnhubSource(cache)
    try:
        fintech_movers = fh.fetch_quotes()
        # Attach catalyst headlines to movers
        news_by_sym = {}
        for n in fintech_news:
            sym = (n.raw_data or {}).get("symbol", "")
            if sym and sym not in news_by_sym:
                news_by_sym[sym] = n.headline.replace(f"[{sym}] ", "")
        for m in fintech_movers:
            m["catalyst"] = news_by_sym.get(m["symbol"], "")
    except Exception:
        fintech_movers = []

    # Social highlights — top 3 by engagement
    social_signals.sort(
        key=lambda s: (s.raw_data or {}).get("engagement", 0), reverse=True,
    )

    text = daily_renderer.render(
        date_str=date_str,
        price_usd=price,
        price_sgd=mdata.get("price_sgd"),
        chg_24h=mdata.get("chg_24h"), chg_7d=mdata.get("chg_7d"),
        ath_usd=mdata.get("ath_usd"),
        fng_value=fng_val, fng_class=fng_cls,
        crypto_news=crypto_news[:6],
        fintech_news=fintech_news[:5],
        social_highlights=social_signals[:3],
        fintech_movers=fintech_movers,
    )

    if print_only:
        print(text)
    else:
        _send(text)


def run_hourly_scan(print_only: bool = False):
    """Hourly scan: curated news brief — top stories from fast sources."""
    raw = _collect_fast_sources()
    items = _pipeline(raw)

    # Keep only actual news stories — exclude bare price quotes,
    # F&G snapshots, and other non-news items.
    news_items = []
    for i in items:
        rd = i.raw_data or {}
        if rd.get("is_quote"):
            continue  # Finnhub stock quotes
        if "fng_value" in rd:
            continue  # Fear & Greed index snapshots
        if i.source == "coingecko" and "BTC $" in i.headline:
            continue  # CoinGecko price snapshots
        news_items.append(i)

    news_items.sort(key=lambda s: s.signal_score, reverse=True)

    # Take top 3-5 items
    top = news_items[:5]
    if not top:
        return  # Nothing worth sending

    messages = hourly_renderer.render(top)
    if not messages:
        return

    if print_only:
        for msg in messages:
            print(msg)
    else:
        for msg in messages:
            _send(msg)


# ── CLI ──

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Signal Intelligence")
    parser.add_argument("command", choices=["weekly", "daily", "hourly"])
    parser.add_argument("--print", dest="print_only", action="store_true")
    args = parser.parse_args()

    if args.command == "weekly":
        run_weekly_update(print_only=args.print_only)
    elif args.command == "daily":
        run_daily_update(print_only=args.print_only)
    elif args.command == "hourly":
        run_hourly_scan(print_only=args.print_only)


if __name__ == "__main__":
    main()
