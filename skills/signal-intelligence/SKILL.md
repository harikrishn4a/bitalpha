# Crypto + FinTech Signal Intelligence

```yaml
name: signal-intelligence
description: >
  BTC-led crypto + fintech signal intelligence. Fetches from 6 API sources,
  scores and tiers signals (FYI / Heads Up / Actionable), produces weekly
  macro updates, daily briefs with chart gating, and hourly alerts when
  significant. All claims include inline source links.
metadata:
  openclaw:
    emoji: "📡"
```

## Commands

- **Weekly Macro Update** — `./bin/run_weekly.sh`
  Full macro regime analysis, BTC snapshot, scenarios, catalysts, fintech brief.

- **Daily Update** — `./bin/run_daily.sh`
  Pricing pulse, conditional chart, "if this then that" playbook.

- **Hourly Scan** — `./bin/run_hourly.sh`
  Only fires when Heads Up or Actionable signals detected.

## Invocation

```
openclaw run signal-intelligence weekly
openclaw run signal-intelligence daily
openclaw run signal-intelligence hourly
```

Or via Telegram: `/signal-intelligence daily`
