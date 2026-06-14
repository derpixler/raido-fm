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
    contributor TEXT,
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

CREATE TABLE IF NOT EXISTS contributor_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT,
    contact TEXT,
    tokens INTEGER DEFAULT 1000,
    ad_contributor TEXT,
    ad_product TEXT,
    ad_key_message TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS token_usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contributor_name TEXT NOT NULL,
    station_slug TEXT NOT NULL,
    role TEXT NOT NULL,
    operation TEXT NOT NULL,
    model TEXT NOT NULL DEFAULT '',
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    latency_ms REAL NOT NULL DEFAULT 0,
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


async def log_ad(db: aiosqlite.Connection, station_slug: str, contributor: str, product: str, key_message: str) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cursor = await db.execute(
        "INSERT INTO ad_log (station_slug, contributor, product, key_message, injected_at) VALUES (?,?,?,?,?)",
        (station_slug, contributor, product, key_message, now),
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


_VALID_TABLES = {"injection_log", "ad_log", "cleanup_log", "generated_personas", "station_registry", "contributor_requests"}

async def cleanup_old_entries(db: aiosqlite.Connection, table: str, category: str = None, max_entries: int = 200) -> int:
    if table not in _VALID_TABLES:
        raise ValueError(f"Invalid table name: {table}")

    if table == "injection_log" and category:
        cursor = await db.execute(
            "SELECT COUNT(*) as c FROM injection_log WHERE category = ?", (category,)
        )
    else:
        cursor = await db.execute(f"SELECT COUNT(*) as c FROM {table}")  # nosec B608
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
            f"DELETE FROM {table} WHERE id IN (SELECT id FROM {table} ORDER BY id ASC LIMIT ?)",  # nosec B608
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


async def add_contributor_request(db: aiosqlite.Connection, name: str, url: str, contact: str, tokens: int, ad_contributor: str, ad_product: str, ad_key_message: str) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cursor = await db.execute(
        "INSERT INTO contributor_requests (name, url, contact, tokens, ad_contributor, ad_product, ad_key_message, status, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (name, url, contact, tokens, ad_contributor, ad_product, ad_key_message, 'pending', now),
    )
    await db.commit()
    return cursor.lastrowid


async def get_contributor_requests(db: aiosqlite.Connection, status: str = None) -> list[dict]:
    if status:
        cursor = await db.execute("SELECT * FROM contributor_requests WHERE status = ? ORDER BY id DESC", (status,))
    else:
        cursor = await db.execute("SELECT * FROM contributor_requests ORDER BY id DESC")
    return [dict(r) for r in await cursor.fetchall()]


async def update_contributor_request(db: aiosqlite.Connection, request_id: int, status: str) -> None:
    await db.execute("UPDATE contributor_requests SET status = ? WHERE id = ?", (status, request_id))
    await db.commit()


async def delete_contributor_request(db: aiosqlite.Connection, request_id: int) -> None:
    await db.execute("DELETE FROM contributor_requests WHERE id = ?", (request_id,))
    await db.commit()


async def log_token_call(
    db: aiosqlite.Connection,
    contributor_name: str,
    station_slug: str,
    role: str,
    operation: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    latency_ms: float,
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cursor = await db.execute(
        "INSERT INTO token_usage_log (contributor_name, station_slug, role, operation, model, prompt_tokens, completion_tokens, total_tokens, latency_ms, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (contributor_name, station_slug, role, operation, model, prompt_tokens, completion_tokens, total_tokens, latency_ms, now),
    )
    await db.commit()
    return cursor.lastrowid


async def get_contributor_usage(db: aiosqlite.Connection, name: str) -> dict:
    cursor = await db.execute(
        "SELECT COUNT(*) as calls, SUM(total_tokens) as total_tokens, SUM(prompt_tokens) as prompt_tokens, SUM(completion_tokens) as completion_tokens, AVG(latency_ms) as avg_latency_ms FROM token_usage_log WHERE contributor_name = ?",
        (name,),
    )
    row = await cursor.fetchone()
    calls = row["calls"] or 0

    cursor = await db.execute(
        "SELECT station_slug, SUM(total_tokens) as tokens, COUNT(*) as calls FROM token_usage_log WHERE contributor_name = ? GROUP BY station_slug ORDER BY tokens DESC",
        (name,),
    )
    by_station = [dict(r) for r in await cursor.fetchall()]

    cursor = await db.execute(
        "SELECT role, SUM(total_tokens) as tokens, COUNT(*) as calls FROM token_usage_log WHERE contributor_name = ? GROUP BY role ORDER BY tokens DESC",
        (name,),
    )
    by_role = [dict(r) for r in await cursor.fetchall()]

    last_row = await (await db.execute(
        "SELECT created_at FROM token_usage_log WHERE contributor_name = ? ORDER BY id DESC LIMIT 1",
        (name,),
    )).fetchone()

    return {
        "contributor_name": name,
        "total_tokens": row["total_tokens"] or 0,
        "prompt_tokens": row["prompt_tokens"] or 0,
        "completion_tokens": row["completion_tokens"] or 0,
        "calls": calls,
        "avg_latency_ms": round(row["avg_latency_ms"] or 0, 1),
        "by_station": by_station,
        "by_role": by_role,
        "last_used_at": last_row["created_at"] if last_row else None,
    }


async def get_contributor_usage_log(db: aiosqlite.Connection, name: str, limit: int = 50) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM token_usage_log WHERE contributor_name = ? ORDER BY id DESC LIMIT ?",
        (name, limit),
    )
    return [dict(r) for r in await cursor.fetchall()]


async def get_all_contributors_usage(db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute(
        "SELECT contributor_name, COUNT(*) as calls, SUM(total_tokens) as total_tokens, MAX(created_at) as last_used_at FROM token_usage_log GROUP BY contributor_name ORDER BY total_tokens DESC"
    )
    return [dict(r) for r in await cursor.fetchall()]
