---
name: btc_digest
description: Weekly BTC Macro & Trend Pack (metrics + chart) and daily 60-second brief. Script-based; run bin/run_weekly.sh or bin/run_daily.sh.
metadata: { "openclaw": { "emoji": "₿" } }
---

# BTC Digest

Generates a weekly "BTC Macro & Trend Pack" with price, trend map, macro dashboard, important dates, news, Learn 1 Thing, and safety tip. Plus a PNG chart (90d price + 50d MA).

## Invocation

To run the weekly digest:
```bash
cd skills/btc_digest && ./bin/run_weekly.sh
```

To run the daily brief:
```bash
cd skills/btc_digest && ./bin/run_daily.sh
```

Use `--print` or `-p` to print output instead of sending:
```bash
./bin/run_weekly.sh --print
./bin/run_daily.sh --print
```

## Prerequisites

- Python 3.11+
- `.env` configured (copy from `.env.example`)
- `OPENCLAW_TO` set for delivery
