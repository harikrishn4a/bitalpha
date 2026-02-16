#!/usr/bin/env bash
# Add system cron for weekly BTC digest (Sun 8AM Singapore).
# Usage: ./scripts/add-btc-weekly-cron.sh
# Then: crontab -e and paste the line printed below.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BITALPHA="$(cd "$SCRIPT_DIR/.." && pwd)"
RUN_WEEKLY="$BITALPHA/skills/btc_digest/bin/run_weekly.sh"

echo "Add this line to crontab (crontab -e):"
echo ""
echo "# BTC Weekly Macro Pack - Sun 8AM Singapore"
echo "0 8 * * 0 cd $BITALPHA/skills/btc_digest && $RUN_WEEKLY"
echo ""
echo "Optional - daily brief (Mon-Fri 8AM Singapore):"
echo "# BTC Daily Brief"
echo "0 8 * * 1-5 cd $BITALPHA/skills/btc_digest && $BITALPHA/skills/btc_digest/bin/run_daily.sh"
