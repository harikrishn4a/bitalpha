#!/usr/bin/env bash
# Run weekly BTC Macro & Trend Pack. Creates venv if needed, generates digest + chart, sends via OpenClaw.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SKILL_ROOT"

VENV="$SKILL_ROOT/.venv"
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
fi
source "$VENV/bin/activate"
pip install -q -r requirements.txt

# Run weekly digest (sends unless --print)
if [ "$1" = "--print" ] || [ "$1" = "-p" ]; then
    python3 -c "
import sys
sys.path.insert(0, '$SKILL_ROOT')
from src.render.weekly_digest import render, main
text, chart = render()
print(text)
if chart:
    print('\n[Chart: ' + chart + ']')
"
else
    python3 -c "
import sys
sys.path.insert(0, '$SKILL_ROOT')
from src.render.weekly_digest import main
main()
"
fi
