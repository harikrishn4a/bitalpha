#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

echo "=== Signal Intelligence Cron Setup ==="
echo ""
echo "Add the following to your crontab (crontab -e):"
echo ""
echo "TZ=Asia/Singapore"
echo "# Weekly: Sunday 8 AM"
echo "0 8 * * 0 cd $ROOT && ./bin/run_weekly.sh"
echo "# Daily: Mon-Fri 8 AM"
echo "0 8 * * 1-5 cd $ROOT && ./bin/run_daily.sh"
echo "# Hourly: every 3 hours (one message per news item when significant)"
echo "0 */3 * * * cd $ROOT && ./bin/run_hourly.sh"
echo ""
