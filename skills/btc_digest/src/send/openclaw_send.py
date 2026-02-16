"""Send digest via OpenClaw CLI."""
import subprocess
import sys
from pathlib import Path

# Add src to path for standalone runs
_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from src.config import OPENCLAW_CHANNEL, OPENCLAW_TO


def send(text: str, chart_path: str | None = None):
    """Send text (and optionally chart) via openclaw message send."""
    if not OPENCLAW_TO:
        print("OPENCLAW_TO not set; skipping send. Use --print to test.", file=sys.stderr)
        return
    cmd = ["openclaw", "message", "send", "--channel", OPENCLAW_CHANNEL, "--target", OPENCLAW_TO, "--message", text]
    if chart_path and Path(chart_path).exists():
        abs_path = str(Path(chart_path).resolve())
        cmd.extend(["--media", abs_path])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        print("openclaw not found in PATH", file=sys.stderr)
        raise
    if result.returncode != 0:
        err = result.stderr or result.stdout or str(result)
        # OpenClaw rejects media if path not in allowed directory; fallback to text-only
        if chart_path and "allowed directory" in err:
            cmd_no_media = ["openclaw", "message", "send", "--channel", OPENCLAW_CHANNEL, "--target", OPENCLAW_TO, "--message", text + "\n\n📊 Chart could not be attached (path restricted). Check CHART_DIR in .env."]
            subprocess.run(cmd_no_media, check=True)
        else:
            print(err, file=sys.stderr)
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
