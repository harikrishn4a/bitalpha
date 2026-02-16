#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .env 2>/dev/null || true
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
python -m openclaw.skills weekly "$@"
