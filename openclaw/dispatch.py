"""Message dispatch via OpenClaw CLI (telegram + email stubs)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def send_telegram(text: str, chart_path: str | None = None,
                  channel: str | None = None, target: str | None = None):
    """Send message via OpenClaw CLI to Telegram."""
    ch = channel or os.getenv("OPENCLAW_CHANNEL", "telegram")
    to = target or os.getenv("OPENCLAW_TO", "")
    if not to:
        print("OPENCLAW_TO not set; skipping send.", file=sys.stderr)
        return

    cmd = ["openclaw", "message", "send", "--channel", ch, "--target", to, "--message", text]
    if chart_path and Path(chart_path).exists():
        cmd.extend(["--media", str(Path(chart_path).resolve())])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        print("openclaw not found in PATH", file=sys.stderr)
        raise

    if result.returncode != 0:
        err = result.stderr or result.stdout or ""
        if chart_path and "allowed directory" in err:
            # Fallback: send without media
            cmd_text = ["openclaw", "message", "send", "--channel", ch, "--target", to,
                        "--message", text + "\n\n[Chart could not be attached]"]
            subprocess.run(cmd_text, check=True)
        else:
            print(err, file=sys.stderr)
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)


def send_email(text: str, subject: str = "Signal Intelligence Alert",
               to: str | None = None):
    """Email dispatch stub. Implement when email is configured."""
    print(f"[EMAIL STUB] To: {to or 'not set'} | Subject: {subject}", file=sys.stderr)
    print(f"[EMAIL STUB] Body length: {len(text)} chars", file=sys.stderr)


def send_alert(text: str, chart_path: str | None = None,
               channels: list[str] | None = None):
    """Send alert via all configured channels."""
    chs = channels or ["telegram"]
    for ch in chs:
        if ch == "telegram":
            send_telegram(text, chart_path)
        elif ch == "email":
            send_email(text)
        else:
            print(f"Unknown channel: {ch}", file=sys.stderr)
