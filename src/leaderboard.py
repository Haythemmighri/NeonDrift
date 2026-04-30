"""
Leaderboard — direct SQLite, no server needed.

All disk I/O runs on a background daemon thread so it never
stalls the 60 FPS game loop.

Database file: leaderboard.db  (created next to main.py)
"""

import sqlite3
import threading
import time
import os

DB_PATH = "leaderboard.db"   # relative to cwd (where main.py lives)


# ── Schema ────────────────────────────────────────────────────────────────────

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS scores (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT    NOT NULL,
    score     INTEGER NOT NULL,
    wave      INTEGER NOT NULL DEFAULT 1,
    submitted TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M', 'now', 'localtime'))
);
"""


def _open_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")   # safe for concurrent access
    conn.execute(_CREATE_SQL)
    conn.commit()
    return conn


# ── Client (used by the game) ─────────────────────────────────────────────────

class LeaderboardClient:
    """
    Thread-safe leaderboard backed by a local SQLite file.

    Game thread only calls:
        client.submit(name, score, wave)  – queues a write, returns instantly
        client.get_entries()              – returns cached top-10 list
        client.get_status()               – "ok" | "loading" | "error"
        client.refresh()                  – force re-read on next tick
    """

    def __init__(self):
        self._lock          = threading.Lock()
        self._entries       = []          # cached list of dicts
        self._status        = "loading"   # loading | ok | error
        self._submit_queue  = []          # [(name, score, wave), ...]
        self._last_fetch    = 0.0
        self._refresh_gap   = 8           # seconds between auto-refreshes
        self._running       = True
        self._conn          = None

        t = threading.Thread(target=self._worker, daemon=True)
        t.start()

    # ── Public API ────────────────────────────────────────────────────────

    def submit(self, name: str, score: int, wave: int):
        """Queue a score insertion. Returns immediately (never blocks)."""
        name = (name or "AAA").strip()[:12]
        with self._lock:
            self._submit_queue.append((name, int(score), int(wave)))

    def get_entries(self):
        """Return a snapshot of the cached top-10 (safe to call every frame)."""
        with self._lock:
            return list(self._entries)

    def get_status(self):
        with self._lock:
            return self._status

    def refresh(self):
        """Trigger an immediate re-read on the next worker tick."""
        self._last_fetch = 0.0

    def shutdown(self):
        self._running = False

    # ── Background worker ─────────────────────────────────────────────────

    def _worker(self):
        try:
            self._conn = _open_db()
        except Exception as exc:
            with self._lock:
                self._status = "error"
            return

        while self._running:
            # 1. Flush queued writes
            with self._lock:
                pending = list(self._submit_queue)
                self._submit_queue.clear()

            for name, score, wave in pending:
                self._insert(name, score, wave)

            # 2. Periodic refresh
            if time.time() - self._last_fetch >= self._refresh_gap:
                self._fetch()

            time.sleep(0.25)

    def _insert(self, name, score, wave):
        try:
            self._conn.execute(
                "INSERT INTO scores (name, score, wave) VALUES (?, ?, ?)",
                (name, score, wave),
            )
            self._conn.commit()
            self._fetch()   # refresh cache immediately after writing
        except Exception:
            with self._lock:
                self._status = "error"

    def _fetch(self):
        self._last_fetch = time.time()
        try:
            rows = self._conn.execute(
                "SELECT name, score, wave, submitted "
                "FROM scores ORDER BY score DESC LIMIT 10"
            ).fetchall()
            entries = [dict(r) for r in rows]
            with self._lock:
                self._entries = entries
                self._status  = "ok"
        except Exception:
            with self._lock:
                self._status = "error"
