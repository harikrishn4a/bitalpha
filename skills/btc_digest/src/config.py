"""Configuration loader for btc_digest. Loads from .env and provides defaults."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from skill root (parent of src/)
SKILL_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(SKILL_ROOT / ".env")

# Paths (resolve to absolute for OpenClaw media allowlist)
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(SKILL_ROOT / "out"))).expanduser().resolve()
# Chart: save to dir OpenClaw accepts. Try /tmp (often allowed); override with CHART_DIR
CHART_DIR = Path(os.getenv("CHART_DIR", "/tmp")).expanduser().resolve()
CACHE_DIR = Path(os.getenv("CACHE_DIR", str(SKILL_ROOT / ".cache"))).expanduser().resolve()
CACHE_TTL_SEC = int(os.getenv("CACHE_TTL_SEC", "300"))

# APIs
FRED_API_KEY = os.getenv("FRED_API_KEY") or ""
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY") or ""
EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY") or ""

# OpenClaw
OPENCLAW_CHANNEL = os.getenv("OPENCLAW_CHANNEL", "telegram")
OPENCLAW_TO = os.getenv("OPENCLAW_TO", "")

# Locale
TIMEZONE = os.getenv("TIMEZONE", "Asia/Singapore")
DIGEST_LANG = os.getenv("DIGEST_LANG", "en")

# RSS (comma-separated)
RSS_FEEDS_RAW = os.getenv("RSS_FEEDS", "")
RSS_FEEDS = [f.strip() for f in RSS_FEEDS_RAW.split(",") if f.strip()]

# Data files
MACRO_EVENTS_PATH = SKILL_ROOT / "macro_events.json"


def ensure_dirs():
    """Create OUTPUT_DIR and CACHE_DIR if they don't exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
