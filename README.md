# Crypto + FinTech Signal Intelligence (BTC-led)

A modular, BTC-led signal intelligence system that fetches from 6 API sources, scores and tiers signals, and delivers actionable insights via Telegram (OpenClaw).

## Architecture

```
data_sources/ → signal_engine/ → outputs/ → openclaw/dispatch
     ↓              ↓               ↓
   6 APIs     score + tier      weekly/daily/hourly
```

**Data Sources:** FRED, CoinGecko, CoinMarketCal, NewsAPI/GDELT, X Trends, Finnhub
**Signal Engine:** Normalize → Dedupe → Score (0-100) → Tier (FYI/Heads Up/Actionable)
**Outputs:** Weekly macro update, daily brief with chart gating, hourly alerts
**Delivery:** Telegram via OpenClaw CLI

## Setup

1. Clone the repo
2. Create virtual environment:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```
5. Run:
   ```bash
   # Weekly update (print to terminal)
   ./bin/run_weekly.sh --print

   # Daily update
   ./bin/run_daily.sh --print

   # Hourly scan
   ./bin/run_hourly.sh --print
   ```
6. Set up cron (optional):
   ```bash
   ./scripts/setup_cron.sh
   ```

## Signal Scoring

Each signal gets scored 0-100 across 4 dimensions:

| Dimension | Range | What it measures |
|-----------|-------|------------------|
| Price impact | 0-30 | How much this could move BTC or markets |
| Novelty | 0-20 | Is this new information or recurring data? |
| Credibility | 0-30 | Source reliability (FRED > CoinGecko > X) |
| Time sensitivity | 0-20 | How soon does this matter? |

## Tiers

- **FYI (0-59):** Informational; no action needed
- **Heads Up (60-79):** Worth monitoring; may need action
- **Actionable (80-100):** Requires attention now

## Chart Gating

Charts are only included when the ChartSignificanceScore >= 70 (based on volatility, regime shift, F&G extremes, and catalyst density). Otherwise:
> "No chart today — nothing materially changed in structure/flows/volatility."

## Tests

```bash
python -m pytest tests/ -v
# or
python tests/test_scoring.py
python tests/test_tiering.py
python tests/test_chart_gate.py
```

## Project Structure

```
bitalpha/
├── config.yaml           # Thresholds, watchlists, schedule
├── data_sources/         # 6 API connectors
├── signal_engine/        # Normalize, score, tier, regime, playbook
├── outputs/              # Weekly/daily/hourly renderers + charts
├── openclaw/             # Skills, dispatch, scheduling
├── storage/              # Cache + SQLite
├── utils/                # Format helpers
├── tests/                # Unit tests
├── examples/             # Sample outputs
├── bin/                  # Shell scripts
└── skills/               # OpenClaw SKILL.md
```
