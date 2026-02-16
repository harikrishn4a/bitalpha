"""Cron / scheduler helpers for OpenClaw integration."""
from __future__ import annotations

import os
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent


def print_cron_entries():
    """Print recommended crontab entries."""
    root = SKILL_ROOT
    print("# ── Signal Intelligence Cron (SGT via TZ) ──")
    print(f"TZ=Asia/Singapore")
    print(f"# Weekly: Sunday 8 AM")
    print(f"0 8 * * 0 cd {root} && ./bin/run_weekly.sh")
    print(f"# Daily: Mon-Fri 8 AM")
    print(f"0 8 * * 1-5 cd {root} && ./bin/run_daily.sh")
    print(f"# Hourly: every hour (only sends if significant)")
    print(f"0 * * * * cd {root} && ./bin/run_hourly.sh")


if __name__ == "__main__":
    print_cron_entries()
