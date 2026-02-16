# BTC Digest (Weekly Macro Pack + Daily Brief)

Script-based skill that generates:
1. **Weekly "BTC Macro & Trend Pack"** — price (comma-formatted), 90d range & ATH context, trend map, **What it means** (plain-English interpretation), macro dashboard, important dates, news, Learn 1 Thing, safety tip, and one PNG chart.
2. **Daily "BTC 60-second" brief** — price, 24h %, F&G, levels, today's macro events.

## Setup

1. Copy `.env.example` to `.env`
2. Set `OPENCLAW_TO` to your Telegram chat ID (e.g. `737798118`)
3. (Optional) Add `FRED_API_KEY` for macro data
4. (Optional) Add `RSS_FEEDS` for news headlines (comma-separated URLs)
5. Edit `macro_events.json` with upcoming FOMC, CPI, NFP, etc.
6. If the chart doesn't attach in Telegram, set `CHART_DIR` to a path OpenClaw allows (default `/tmp`).

```bash
cp .env.example .env
# Edit .env
```

## Run

**Weekly digest:**
```bash
./bin/run_weekly.sh
```

**Daily brief:**
```bash
./bin/run_daily.sh
```

**Test locally (print, no send):**
```bash
./bin/run_weekly.sh --print
./bin/run_daily.sh --print
```

## Cron

**System cron** (recommended for script-based digest):

```bash
# Weekly: Sun 8AM Singapore
0 8 * * 0 cd /Users/hari/bitalpha/skills/btc_digest && ./bin/run_weekly.sh

# Daily: Mon–Fri 8AM Singapore
0 8 * * 1-5 cd /Users/hari/bitalpha/skills/btc_digest && ./bin/run_daily.sh
```

Or use the helper script:
```bash
./scripts/add-btc-weekly-cron.sh
```

## Sample Output (SAMPLE)

```
# ₿ BTC Weekly Macro & Trend Pack — Sun 16 Feb 2026, 09:00 SGT

**Price now:** $90,123 USD / $121,500 SGD
**7d change:** (-2.1%) | YTD: +12.3%
**Fear & Greed:** 8 (Extreme Fear) | 30d range: 5–20

---

## Important Dates — Macro Events
- **2026-03-18** — FOMC decision (Rates; risk assets)
- **2026-03-26** — US CPI release (Inflation; rate expectations)

---

## BTC Trend Map
**Regime:** Range
**Levels:** S2 88,000 | S1 89,500 | Pivot 90,000 | R1 92,000 | R2 94,000

## Macro Dashboard
(macro data unavailable — add FRED_API_KEY)

## Top Headlines
News disabled (no RSS sources configured).

## Learn 1 Thing (90 seconds)
**What moves BTC? liquidity vs narratives**
- Like a boat on tides: liquidity is the water, narratives are the wind.
- Misconception to avoid: Only fundamentals matter — liquidity often leads.

**Safety tip:** Seed phrase: Write it down, never store digitally.

*Digital payment tokens are high-risk; this is informational, not financial advice.*
```
