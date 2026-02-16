#!/bin/bash
# Add daily BTC trend alert cron job (8AM Singapore)
# Usage: ./scripts/add-cron-job.sh YOUR_CHAT_ID
# Example: ./scripts/add-cron-job.sh 123456789

CHAT_ID="${1:?Usage: $0 YOUR_TELEGRAM_CHAT_ID}"

openclaw cron add \
  --name "btc-daily" \
  --cron "0 8 * * *" \
  --tz "Asia/Singapore" \
  --session isolated \
  --message "Run the bitcoin-trend-alert skill: fetch BTC price (USD/SGD), analyze 24h/7d trend, scrape X (web_search + Nitter), Reddit, and news. Generate the 1-2-3 digest and send it to Telegram." \
  --announce \
  --channel telegram \
  --to "$CHAT_ID"

echo ""
echo "Verify with: openclaw cron list"
echo "Test now:    openclaw cron run btc-daily"
