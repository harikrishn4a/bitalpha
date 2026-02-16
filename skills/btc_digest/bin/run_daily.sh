#!/usr/bin/env bash
# Run daily BTC 60-second brief.
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

if [ "$1" = "--print" ] || [ "$1" = "-p" ]; then
    python3 -c "
import sys
sys.path.insert(0, '$SKILL_ROOT')
from src.render.daily_brief import render
print(render())
"
else
    python3 -c "
import sys
sys.path.insert(0, '$SKILL_ROOT')
from src.render.daily_brief import main
main()
"
fi
