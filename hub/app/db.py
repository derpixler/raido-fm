from __future__ import annotations

import aiosqlite
import json
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("data/hub.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS generated_personas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    persona_yaml TEXT NOT NULL,
    tracks_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS station_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    port INTEGER NOT NULL,
    container_name TEXT,
    protected INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    idle_since TEXT
);

CREATE TABLE IF NOT EXISTS ad_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_slug TEXT NOT NULL,
    sponsor TEXT,
    product TEXT,
    key_message TEXT,
    injected_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS injection_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_slug TEXT NOT NULL,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    injected_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cleanup_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    deleted_count INTEGER NOT NULL,
    deleted_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sponsor_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT,
    contact TEXT,
    tokens INTEGER DEFAULT 1000,
    ad_sponsor TEXT,
    ad_product TEXT,
    ad_key_message TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT NOT NULL
);
"""


async def get_db() -> aiosqlite.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.executescript(_SCHEMA)
    await db.commit()
    return db


async def save_persona(db: aiosqlite.Connection, station_id: str, slug: str, persona_yaml: str, tracks_json: str | None = None) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cursor = await db.execute(
        "INSERT OR REPLACE INTO generated_personas (station_id, slug, persona_yaml, tracks_json, created_at) VALUES (?,?,?,?,?)",
        (station_id, slug, persona_yaml, tracks_json, now),
    )
    await db.commit()
    return cursor.lastrowid


async def get_personas(db: aiosqlite.Connection, limit: int = 20) -> list[dict]:
    cursor = await db.execute("SELECT * FROM generated_personas ORDER BY id DESC LIMIT ?", (limit,))
    return [dict(r) for r in await cursor.fetchall()]


async def get_persona_by_id(db: aiosqlite.Connection, persona_id: int) -> dict | None:
    cursor = await db.execute("SELECT * FROM generated_personas WHERE id = ?", (persona_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def count_personas(db: aiosqlite.Connection) -> int:
    cursor = await db.execute("SELECT COUNT(*) as c FROM generated_personas")
    row = await cursor.fetchone()
    return row["c"] if row else 0


async def delete_persona(db: aiosqlite.Connection, persona_id: int) -> bool:
    cursor = await db.execute("DELETE FROM generated_personas WHERE id = ?", (persona_id,))
    await db.commit()
    return cursor.rowcount > 0


async def register_station(db: aiosqlite.Connection, station_id: str, slug: str, port: int, container_name: str, protected: bool = False) -> None:
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT OR REPLACE INTO station_registry (station_id, slug, port, container_name, protected, created_at) VALUES (?,?,?,?,?,?)",
        (station_id, slug, port, container_name, int(protected), now),
    )
    await db.commit()


async def unregister_station(db: aiosqlite.Connection, station_id: str) -> None:
    await db.execute("DELETE FROM station_registry WHERE station_id = ?", (station_id,))
    await db.commit()


async def get_registered_stations(db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute("SELECT * FROM station_registry ORDER BY created_at")
    return [dict(r) for r in await cursor.fetchall()]


async def get_station_by_slug(db: aiosqlite.Connection, slug: str) -> dict | None:
    cursor = await db.execute("SELECT * FROM station_registry WHERE slug = ?", (slug,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def set_idle_since(db: aiosqlite.Connection, station_id: str, idle_since: str | None) -> None:
    await db.execute("UPDATE station_registry SET idle_since = ? WHERE station_id = ?", (idle_since, station_id))
    await db.commit()


async def log_ad(db: aiosqlite.Connection, station_slug: str, sponsor: str, product: str, key_message: str) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cursor = await db.execute(
        "INSERT INTO ad_log (station_slug, sponsor, product, key_message, injected_at) VALUES (?,?,?,?,?)",
        (station_slug, sponsor, product, key_message, now),
    )
    await db.commit()
    return cursor.lastrowid


async def get_ads(db: aiosqlite.Connection, limit: int = 50) -> list[dict]:
    cursor = await db.execute("SELECT * FROM ad_log ORDER BY id DESC LIMIT ?", (limit,))
    return [dict(r) for r in await cursor.fetchall()]


async def log_injection(db: aiosqlite.Connection, station_slug: str, station_port: int = 0, category: str = "", content: str = "", stimulus_id: int = None) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cursor = await db.execute(
        "INSERT INTO injection_log (station_slug, station_port, category, content, stimulus_id, status, injected_at) VALUES (?,?,?,?,?,?,?)",
        (station_slug, station_port, category, content, stimulus_id, 'pending', now),
    )
    await db.commit()
    return cursor.lastrowid


async def get_injections(db: aiosqlite.Connection, category: str = None, limit: int = 50) -> list[dict]:
    if category:
        cursor = await db.execute(
            "SELECT * FROM injection_log WHERE category = ? ORDER BY id DESC LIMIT ?", (category, limit)
        )
    else:
        cursor = await db.execute("SELECT * FROM injection_log ORDER BY id DESC LIMIT ?", (limit,))
    return [dict(r) for r in await cursor.fetchall()]


async def get_pending_injections(db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute("SELECT * FROM injection_log WHERE status = 'pending' OR status = 'timeout'")
    return [dict(r) for r in await cursor.fetchall()]


async def get_visible_injections(db: aiosqlite.Connection, category: str = None, limit: int = 50) -> list[dict]:
    if category:
        cursor = await db.execute(
            "SELECT * FROM injection_log WHERE category = ? AND status != 'timeout' ORDER BY id DESC LIMIT ?", (category, limit)
        )
    else:
        cursor = await db.execute("SELECT * FROM injection_log WHERE status != 'timeout' ORDER BY id DESC LIMIT ?", (limit,))
    return [dict(r) for r in await cursor.fetchall()]


async def update_injection_status(db: aiosqlite.Connection, injection_id: int, status: str, moderation_text: str = None, flagged: bool = False, flag_reason: str = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "UPDATE injection_log SET status = ?, moderation_text = ?, flagged = ?, flag_reason = ?, used_at = ? WHERE id = ?",
        (status, moderation_text or None, int(flagged), flag_reason or None, now, injection_id),
    )
    await db.commit()


async def cleanup_old_entries(db: aiosqlite.Connection, table: str, category: str = None, max_entries: int = 200) -> int:
    if table == "injection_log" and category:
        cursor = await db.execute(
            "SELECT COUNT(*) as c FROM injection_log WHERE category = ?", (category,)
        )
    else:
        cursor = await db.execute(f"SELECT COUNT(*) as c FROM {table}")
    row = await cursor.fetchone()
    total = row["c"] if row else 0
    overflow = total - max_entries
    if overflow <= 0:
        return 0

    if table == "injection_log" and category:
        await db.execute(
            "DELETE FROM injection_log WHERE id IN (SELECT id FROM injection_log WHERE category = ? ORDER BY id ASC LIMIT ?)",
            (category, overflow),
        )
    else:
        await db.execute(
            f"DELETE FROM {table} WHERE id IN (SELECT id FROM {table} ORDER BY id ASC LIMIT ?)",
            (overflow,),
        )
    await db.commit()

    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO cleanup_log (table_name, deleted_count, deleted_at) VALUES (?,?,?)",
        (f"{table}:{category}" if category else table, overflow, now),
    )
    await db.commit()
    return overflow


async def add_sponsor_request(db: aiosqlite.Connection, name: str, url: str, contact: str, tokens: int, ad_sponsor: str, ad_product: str, ad_key_message: str) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cursor = await db.execute(
        "INSERT INTO sponsor_requests (name, url, contact, tokens, ad_sponsor, ad_product, ad_key_message, status, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (name, url, contact, tokens, ad_sponsor, ad_product, ad_key_message, 'pending', now),
    )
    await db.commit()
    return cursor.lastrowid


async def get_sponsor_requests(db: aiosqlite.Connection, status: str = None) -> list[dict]:
    if status:
        cursor = await db.execute("SELECT * FROM sponsor_requests WHERE status = ? ORDER BY id DESC", (status,))
    else:
        cursor = await db.execute("SELECT * FROM sponsor_requests ORDER BY id DESC")
    return [dict(r) for r in await cursor.fetchall()]


async def update_sponsor_request(db: aiosqlite.Connection, request_id: int, status: str) -> None:
    await db.execute("UPDATE sponsor_requests SET status = ? WHERE id = ?", (status, request_id))
    await db.commit()
