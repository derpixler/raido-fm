from __future__ import annotations

import aiosqlite
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_DIR = Path(os.getenv("DB_DIR", "data"))
DB_PATH: Path = DB_DIR / "radio.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS play_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL,
    artist TEXT NOT NULL,
    title TEXT NOT NULL,
    genre TEXT NOT NULL,
    played_at TEXT NOT NULL,
    duration INTEGER NOT NULL,
    phase TEXT
);

CREATE TABLE IF NOT EXISTS external_stimuli (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'chat',
    raw_text TEXT,
    raw_json TEXT,
    sanitized_text TEXT,
    sanitized_at TEXT,
    used_at TEXT,
    was_flagged INTEGER DEFAULT 0,
    flag_reason TEXT
);

CREATE TABLE IF NOT EXISTS broadcast_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS station_meta (
    station_id TEXT PRIMARY KEY,
    generated_name TEXT,
    created_at TEXT NOT NULL
);
"""

_MIGRATION = """
-- Migrate old singleton station_meta to new schema
DROP TABLE IF EXISTS station_meta;
CREATE TABLE IF NOT EXISTS station_meta (
    station_id TEXT PRIMARY KEY,
    generated_name TEXT,
    created_at TEXT NOT NULL
);
"""


async def get_db(station_id: str = "radio") -> aiosqlite.Connection:
    global DB_PATH
    DB_PATH = DB_DIR / f"{station_id}.db"
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(str(DB_PATH))
    conn.row_factory = aiosqlite.Row

    cursor = await conn.execute("SELECT sql FROM sqlite_master WHERE name='station_meta'")
    row = await cursor.fetchone()
    if row and "station_id" not in (row["sql"] or ""):
        await conn.executescript(_MIGRATION)

    await conn.executescript(_SCHEMA)
    await conn.commit()
    return conn


async def log_play(db: aiosqlite.Connection, track: dict, phase: str | None = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO play_history (track_id, artist, title, genre, played_at, duration, phase) VALUES (?,?,?,?,?,?,?)",
        (track["id"], track["artist"], track["title"], track["genre"], now, track["duration"], phase),
    )
    await db.commit()


async def get_recent_track_ids(db: aiosqlite.Connection, hours: int = 4) -> list[int]:
    cursor = await db.execute(
        "SELECT track_id FROM play_history WHERE played_at > datetime('now', ?)",
        (f"-{hours} hours",),
    )
    rows = await cursor.fetchall()
    return [r["track_id"] for r in rows]


async def get_last_genres(db: aiosqlite.Connection, n: int = 2) -> list[str]:
    cursor = await db.execute(
        "SELECT genre FROM play_history ORDER BY id DESC LIMIT ?", (n,)
    )
    rows = await cursor.fetchall()
    return [r["genre"] for r in rows]


async def get_last_energies(db: aiosqlite.Connection, n: int = 2) -> list[float]:
    cursor = await db.execute(
        "SELECT track_id FROM play_history ORDER BY id DESC LIMIT ?", (n,)
    )
    rows = await cursor.fetchall()
    return [r["track_id"] for r in rows]


async def insert_stimulus(
    db: aiosqlite.Connection,
    category: str,
    raw_text: str | None,
    raw_json: str | None,
    sanitized_text: str | None,
    was_flagged: bool = False,
    flag_reason: str | None = None,
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cursor = await db.execute(
        "INSERT INTO external_stimuli (category, raw_text, raw_json, sanitized_text, sanitized_at, was_flagged, flag_reason) VALUES (?,?,?,?,?,?,?)",
        (category, raw_text, raw_json, sanitized_text, now, int(was_flagged), flag_reason),
    )
    await db.commit()
    return cursor.lastrowid


async def get_pending_stimuli(
    db: aiosqlite.Connection,
    category: str | None = None,
    exclude_category: str | None = None,
) -> list[dict]:
    query = "SELECT * FROM external_stimuli WHERE used_at IS NULL AND was_flagged = 0"
    params: list = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if exclude_category:
        query += " AND category != ?"
        params.append(exclude_category)
    query += " ORDER BY id"
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def mark_stimuli_used(db: aiosqlite.Connection, ids: list[int]) -> None:
    if not ids:
        return
    now = datetime.now(timezone.utc).isoformat()
    placeholders = ",".join("?" for _ in ids)
    await db.execute(
        f"UPDATE external_stimuli SET used_at = ? WHERE id IN ({placeholders})",
        [now, *ids],
    )
    await db.commit()


async def log_broadcast(db: aiosqlite.Connection, event_type: str, payload: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO broadcast_log (event_type, payload, created_at) VALUES (?,?,?)",
        (event_type, json.dumps(payload, ensure_ascii=False), now),
    )
    await db.commit()


async def get_station_name(db: aiosqlite.Connection, station_id: str | None = None) -> str | None:
    if not station_id:
        return None
    cursor = await db.execute(
        "SELECT generated_name FROM station_meta WHERE station_id = ?", (station_id,)
    )
    row = await cursor.fetchone()
    return row["generated_name"] if row else None


async def set_station_name(db: aiosqlite.Connection, station_id: str, name: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO station_meta (station_id, generated_name, created_at) VALUES (?, ?, ?) "
        "ON CONFLICT(station_id) DO UPDATE SET generated_name = excluded.generated_name",
        (station_id, name, now),
    )
    await db.commit()


async def reset_db(db: aiosqlite.Connection, regenerate_name: bool = False, station_id: str | None = None) -> None:
    await db.execute("DELETE FROM play_history")
    await db.execute("DELETE FROM external_stimuli")
    await db.execute("DELETE FROM broadcast_log")
    if regenerate_name and station_id:
        await db.execute("DELETE FROM station_meta WHERE station_id = ?", (station_id,))
    elif regenerate_name:
        await db.execute("DELETE FROM station_meta")
    await db.commit()
