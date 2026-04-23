"""SQLite state persistence for Fishing Frenzy Agent."""

import json
import os
import sqlite3
import time
from pathlib import Path

STATE_DIR = Path.home() / ".fishing-frenzy-agent"
DB_PATH = STATE_DIR / "state.db"


def _ensure_dir():
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    _ensure_dir()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _init_tables(conn)
    return conn


def _init_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS auth (
            key TEXT PRIMARY KEY,
            value TEXT,
            expires_at INTEGER
        );

        CREATE TABLE IF NOT EXISTS wallet (
            address TEXT PRIMARY KEY,
            private_key TEXT
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT,
            ended_at TEXT,
            fish_caught INTEGER DEFAULT 0,
            gold_earned REAL DEFAULT 0,
            xp_earned INTEGER DEFAULT 0,
            energy_spent INTEGER DEFAULT 0,
            strategy TEXT
        );

        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT,
            cached_at INTEGER
        );

        CREATE TABLE IF NOT EXISTS action_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            timestamp TEXT,
            action TEXT,
            params TEXT,
            result TEXT,
            gold_before REAL,
            gold_after REAL,
            energy_before INTEGER,
            energy_after INTEGER
        );
    """)
    conn.commit()


# --- Auth ---

def save_auth(access_token: str, refresh_token: str, user_id: str,
              privy_token: str = None):
    conn = get_connection()
    try:
        now = int(time.time())
        conn.execute(
            "INSERT OR REPLACE INTO auth (key, value, expires_at) VALUES (?, ?, ?)",
            ("access_token", access_token, now + 1800)
        )
        conn.execute(
            "INSERT OR REPLACE INTO auth (key, value, expires_at) VALUES (?, ?, ?)",
            ("refresh_token", refresh_token, now + 2592000)
        )
        conn.execute(
            "INSERT OR REPLACE INTO auth (key, value, expires_at) VALUES (?, ?, ?)",
            ("user_id", user_id, 0)
        )
        if privy_token:
            conn.execute(
                "INSERT OR REPLACE INTO auth (key, value, expires_at) VALUES (?, ?, ?)",
                ("privy_token", privy_token, now + 3600)
            )
        conn.commit()
    finally:
        conn.close()


def get_auth(key: str) -> str | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT value, expires_at FROM auth WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        if row["expires_at"] > 0 and row["expires_at"] < int(time.time()):
            return None
        return row["value"]
    finally:
        conn.close()


def get_all_auth() -> dict:
    return {
        "access_token": get_auth("access_token"),
        "refresh_token": get_auth("refresh_token"),
        "user_id": get_auth("user_id"),
        "privy_token": get_auth("privy_token"),
    }


# --- Wallet ---

def save_wallet(address: str, private_key: str):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO wallet (address, private_key) VALUES (?, ?)",
            (address, private_key)
        )
        conn.commit()
    finally:
        conn.close()


def get_wallet() -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT address, private_key FROM wallet LIMIT 1").fetchone()
        if row is None:
            return None
        return {"address": row["address"], "private_key": row["private_key"]}
    finally:
        conn.close()


# --- Sessions ---

def start_session(strategy: str = "balanced") -> int:
    conn = get_connection()
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute(
            "INSERT INTO sessions (started_at, strategy) VALUES (?, ?)",
            (now, strategy)
        )
        session_id = cursor.lastrowid
        conn.commit()
        return session_id
    finally:
        conn.close()


def update_session(session_id: int, fish_caught: int = 0, gold_earned: float = 0,
                   xp_earned: int = 0, energy_spent: int = 0):
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE sessions SET
                fish_caught = fish_caught + ?,
                gold_earned = gold_earned + ?,
                xp_earned = xp_earned + ?,
                energy_spent = energy_spent + ?
            WHERE id = ?
        """, (fish_caught, gold_earned, xp_earned, energy_spent, session_id))
        conn.commit()
    finally:
        conn.close()


def end_session(session_id: int):
    conn = get_connection()
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "UPDATE sessions SET ended_at = ? WHERE id = ?", (now, session_id)
        )
        conn.commit()
    finally:
        conn.close()


def get_session_history(limit: int = 10) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_lifetime_stats() -> dict:
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT
                COUNT(*) as total_sessions,
                COALESCE(SUM(fish_caught), 0) as total_fish,
                COALESCE(SUM(gold_earned), 0) as total_gold,
                COALESCE(SUM(xp_earned), 0) as total_xp,
                COALESCE(SUM(energy_spent), 0) as total_energy
            FROM sessions
        """).fetchone()
        return dict(row)
    finally:
        conn.close()


# --- Action Log ---

def log_action(action: str, params: dict = None, result: dict = None,
               gold_before: float = None, gold_after: float = None,
               energy_before: int = None, energy_after: int = None,
               session_id: int = None):
    """Log a game action with optional pre/post state snapshots."""
    conn = get_connection()
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """INSERT INTO action_log
               (session_id, timestamp, action, params, result,
                gold_before, gold_after, energy_before, energy_after)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session_id, now, action,
             json.dumps(params) if params else None,
             json.dumps(result) if result else None,
             gold_before, gold_after, energy_before, energy_after)
        )
        conn.commit()
    finally:
        conn.close()


def get_action_log(session_id: int = None, limit: int = 50) -> list[dict]:
    """Get recent action log entries, optionally filtered by session."""
    conn = get_connection()
    try:
        if session_id:
            rows = conn.execute(
                "SELECT * FROM action_log WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM action_log ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# --- Device ID ---

def get_or_create_device_id() -> str:
    """Get a persistent device ID, creating one if it doesn't exist.

    This ensures the same agent installation always sends the same deviceId
    across logins, making it easy to track agent sessions on the backend.
    """
    device_id = get_auth("device_id")
    if device_id:
        return device_id
    import uuid
    device_id = str(uuid.uuid4())
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO auth (key, value, expires_at) VALUES (?, ?, ?)",
            ("device_id", device_id, 0)  # expires_at=0 means permanent
        )
        conn.commit()
    finally:
        conn.close()
    return device_id


# --- Cache ---

def set_cache(key: str, value: any, ttl: int = 300):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO cache (key, value, cached_at) VALUES (?, ?, ?)",
            (key, json.dumps(value), int(time.time()))
        )
        conn.commit()
    finally:
        conn.close()


def get_cache(key: str, ttl: int = 300) -> any:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT value, cached_at FROM cache WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        if int(time.time()) - row["cached_at"] > ttl:
            return None
        return json.loads(row["value"])
    finally:
        conn.close()


# --- Summary (for SKILL.md dynamic context) ---

def get_summary() -> str:
    wallet = get_wallet()
    auth = get_all_auth()
    stats = get_lifetime_stats()
    recent = get_session_history(3)

    lines = []
    if wallet:
        lines.append(f"Wallet: {wallet['address']}")
    else:
        lines.append("Wallet: Not created yet")

    if auth["user_id"]:
        lines.append(f"User ID: {auth['user_id']}")
        lines.append(f"Auth: {'Active' if auth['access_token'] else 'Expired (needs refresh)'}")
    else:
        lines.append("Account: Not set up yet")

    lines.append(f"\nLifetime Stats:")
    lines.append(f"  Sessions: {stats['total_sessions']}")
    lines.append(f"  Fish Caught: {stats['total_fish']}")
    lines.append(f"  Gold Earned: {stats['total_gold']:.0f}")
    lines.append(f"  XP Earned: {stats['total_xp']}")
    lines.append(f"  Energy Spent: {stats['total_energy']}")

    if recent:
        lines.append(f"\nRecent Sessions:")
        for s in recent:
            lines.append(
                f"  #{s['id']}: {s['fish_caught']} fish, "
                f"{s['gold_earned']:.0f} gold, {s['xp_earned']} XP "
                f"({s['strategy'] or 'unknown'})"
            )

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if "--summary" in sys.argv:
        print(get_summary())
    else:
        print(f"State DB: {DB_PATH}")
        print(f"Exists: {DB_PATH.exists()}")
        if DB_PATH.exists():
            print(get_summary())
