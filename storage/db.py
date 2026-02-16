"""Lightweight SQLite store for signal history and regime snapshots."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    category TEXT NOT NULL,
    headline TEXT NOT NULL,
    body TEXT,
    url TEXT,
    timestamp TEXT NOT NULL,
    signal_score INTEGER NOT NULL,
    tier TEXT NOT NULL,
    why TEXT,
    raw_data TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_signals_ts ON signals(timestamp);
CREATE INDEX IF NOT EXISTS idx_signals_tier ON signals(tier);

CREATE TABLE IF NOT EXISTS regime_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    regime_tag TEXT NOT NULL,
    drivers TEXT NOT NULL,
    delta TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_regime_date ON regime_snapshots(date);
"""


class SignalDB:
    """Thin wrapper around SQLite for signal persistence."""

    def __init__(self, db_path: str | Path):
        self.path = Path(db_path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)

    # ── Signals ──

    def upsert_signal(self, item: dict):
        """Insert or replace a signal item dict."""
        self.conn.execute(
            """INSERT OR REPLACE INTO signals
               (id, source, category, headline, body, url, timestamp,
                signal_score, tier, why, raw_data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                item["id"], item["source"], item["category"],
                item["headline"], item.get("body", ""),
                item.get("url", ""), item["timestamp"],
                item["signal_score"], item["tier"],
                json.dumps(item.get("why_you_got_this", [])),
                json.dumps(item.get("raw_data", {})),
            ),
        )
        self.conn.commit()

    def signal_exists(self, signal_id: str) -> bool:
        row = self.conn.execute("SELECT 1 FROM signals WHERE id = ?", (signal_id,)).fetchone()
        return row is not None

    def recent_signal_ids(self, hours: int = 48) -> set[str]:
        """Return IDs of signals seen in the last N hours."""
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        rows = self.conn.execute(
            "SELECT id FROM signals WHERE created_at >= ?", (cutoff,)
        ).fetchall()
        return {r["id"] for r in rows}

    def clear_signals(self):
        """Remove all rows from signals table. Use for testing so dedupe sees no prior IDs."""
        self.conn.execute("DELETE FROM signals")
        self.conn.commit()

    def signals_by_tier(self, tier: str, limit: int = 50) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM signals WHERE tier = ? ORDER BY timestamp DESC LIMIT ?",
            (tier, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Regime ──

    def save_regime(self, date: str, tag: str, drivers: dict, delta: str | None = None):
        self.conn.execute(
            "INSERT INTO regime_snapshots (date, regime_tag, drivers, delta) VALUES (?, ?, ?, ?)",
            (date, tag, json.dumps(drivers), delta or ""),
        )
        self.conn.commit()

    def latest_regime(self) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM regime_snapshots ORDER BY date DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["drivers"] = json.loads(d["drivers"])
        return d

    def close(self):
        self.conn.close()
