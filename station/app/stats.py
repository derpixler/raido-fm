from __future__ import annotations

import time

from . import db, dj_agent, llm

_start_time = time.monotonic()


def _uptime_seconds() -> int:
    return int(time.monotonic() - _start_time)


async def get_stats(db_conn, subscriber_count: int = 0) -> dict:
    llm_usage = llm.get_usage()

    total_tokens_in = sum(v["prompt_tokens"] for v in llm_usage.values())
    total_tokens_out = sum(v["completion_tokens"] for v in llm_usage.values())
    total_calls = sum(v["calls"] for v in llm_usage.values())
    total_errors = sum(v["errors"] for v in llm_usage.values())

    tracks_played = 0
    moderations = 0
    guard_blocks = 0
    ads_played = 0
    stimuli_total = 0
    stimuli_flagged = 0
    stimuli_pending = 0

    if db_conn:
        cur = await db_conn.execute("SELECT COUNT(*) as c FROM play_history")
        row = await cur.fetchone()
        tracks_played = row["c"] if row else 0

        cur = await db_conn.execute("SELECT COUNT(*) as c FROM broadcast_log WHERE event_type = 'moderation'")
        row = await cur.fetchone()
        moderations = row["c"] if row else 0

        cur = await db_conn.execute("SELECT COUNT(*) as c FROM broadcast_log WHERE event_type = 'guard_block'")
        row = await cur.fetchone()
        guard_blocks = row["c"] if row else 0

        cur = await db_conn.execute("SELECT COUNT(*) as c FROM broadcast_log WHERE event_type = 'ad'")
        row = await cur.fetchone()
        ads_played = row["c"] if row else 0

        cur = await db_conn.execute("SELECT COUNT(*) as c FROM external_stimuli")
        row = await cur.fetchone()
        stimuli_total = row["c"] if row else 0

        cur = await db_conn.execute("SELECT COUNT(*) as c FROM external_stimuli WHERE was_flagged = 1")
        row = await cur.fetchone()
        stimuli_flagged = row["c"] if row else 0

        cur = await db_conn.execute("SELECT COUNT(*) as c FROM external_stimuli WHERE used_at IS NULL AND was_flagged = 0")
        row = await cur.fetchone()
        stimuli_pending = row["c"] if row else 0

    return {
        "uptime_s": _uptime_seconds(),
        "hours_broadcast": dj_agent._hour_count,
        "subscribers": subscriber_count,
        "tracks": {
            "library": len(dj_agent.get_tracks()),
            "played": tracks_played,
        },
        "broadcast": {
            "moderations": moderations,
            "guard_blocks": guard_blocks,
            "ads": ads_played,
        },
        "stimuli": {
            "total": stimuli_total,
            "flagged": stimuli_flagged,
            "pending": stimuli_pending,
        },
        "llm": {
            "calls": total_calls,
            "errors": total_errors,
            "tokens_in": total_tokens_in,
            "tokens_out": total_tokens_out,
            "by_role": llm_usage,
        },
    }
