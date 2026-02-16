# Bitcoin Trend Alert (OpenClaw Skill)

Monitors BTC trends with extensive web scraping (X, Reddit, news), generates educational 1-2-3 digest, sends Telegram alerts.

## Project structure

```
bitalpha/
├── README.md           # This file
├── SETUP.md            # Telegram pairing and setup
├── .gitignore
├── scripts/
│   └── add-cron-job.sh # Add daily 8AM SGT cron job
└── skills/
    └── bitcoin-trend-alert/
        ├── SKILL.md         # Skill instructions (OpenClaw loads from here)
        ├── price_fetch.py   # Optional CoinGecko fetcher
        └── references/
            └── sources.md   # Scraping URLs
```

OpenClaw is configured to load skills from `bitalpha/skills/` via `skills.load.extraDirs`.

## Quick start

1. **Pair Telegram**: See [SETUP.md](SETUP.md)
2. **Add cron** (daily 8AM SGT): `./scripts/add-cron-job.sh 737798118`

## Manual test

- **Telegram**: Message @bit_alphabot `/bitcoin-trend-alert` or "Run the bitcoin trend alert skill"
- **TUI**: `openclaw tui` → "Run the bitcoin-trend-alert skill and send the result to my Telegram"

## Verify

```bash
openclaw skills list    # bitcoin-trend-alert should show ✓ ready
openclaw cron list      # after adding cron
```
