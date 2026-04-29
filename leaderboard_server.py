"""
NEON DRIFT — Leaderboard Server
================================
Standalone Flask + SQLite leaderboard API.

Run:
    python leaderboard_server.py

Endpoints:
    GET  /scores          → JSON list of top-10 scores
    POST /scores          → Submit a score  {name, score, wave}
    GET  /health          → Server health check

By default runs on http://localhost:5000
"""

import sqlite3
import re
from flask import Flask, request, jsonify

DB_PATH = "leaderboard.db"
app = Flask(__name__)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                name      TEXT    NOT NULL,
                score     INTEGER NOT NULL,
                wave      INTEGER NOT NULL DEFAULT 1,
                submitted TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/scores", methods=["GET"])
def get_scores():
    limit = min(int(request.args.get("limit", 10)), 50)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT name, score, wave, submitted FROM scores "
            "ORDER BY score DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/scores", methods=["POST"])
def post_score():
    data = request.get_json(silent=True) or {}

    name  = str(data.get("name",  "AAA")).strip()[:12]
    score = int(data.get("score", 0))
    wave  = int(data.get("wave",  1))

    # Sanitize name: letters, digits, spaces only
    name = re.sub(r"[^A-Za-z0-9 _\-]", "", name) or "AAA"

    if score < 0 or wave < 1:
        return jsonify({"error": "Invalid data"}), 400

    with get_db() as conn:
        conn.execute(
            "INSERT INTO scores (name, score, wave) VALUES (?, ?, ?)",
            (name, score, wave),
        )
        conn.commit()

    return jsonify({"status": "ok", "name": name, "score": score}), 201


if __name__ == "__main__":
    init_db()
    print("┌─────────────────────────────────────────┐")
    print("│  NEON DRIFT  —  Leaderboard Server       │")
    print("│  Running on  http://localhost:5000        │")
    print("│  Press Ctrl+C to stop                    │")
    print("└─────────────────────────────────────────┘")
    app.run(host="0.0.0.0", port=5000, debug=False)
