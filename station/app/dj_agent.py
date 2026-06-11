from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from . import db, llm, streamguard
from .persona import get_persona, build_system_prompt, build_ad_prompt, build_naming_prompt, set_resolved_name

logger = logging.getLogger(__name__)

_DEMO_TIME_SCALE = float(os.getenv("TIME_SCALE", "60"))
_mode = "demo"
TIME_SCALE = _DEMO_TIME_SCALE

GRID = [
    (0, "opening", True),
    (5, "track", False),
    (12, "short_moderation", True),
    (20, "long_moderation", True),
    (30, "impulse", True),
    (38, "track", False),
    (45, "track", False),
    (52, "short_moderation", True),
    (58, "closing", True),
]

_tracks: list[dict] = []
_running = False
_broadcast_queue: asyncio.Queue | None = None
_hour_count = 0


def _load_tracks() -> list[dict]:
    global _tracks
    p = get_persona()
    filename = p.get("tracks_file", "tracks.json")
    path = Path(__file__).parent / filename
    if not path.exists():
        path = Path("/app/personas") / filename
    if not path.exists():
        path = Path(__file__).parent / "tracks.json"
    with open(path) as f:
        _tracks = json.load(f)
    return _tracks


def get_tracks() -> list[dict]:
    if not _tracks:
        _load_tracks()
    return _tracks


def reload_tracks() -> list[dict]:
    global _tracks
    _tracks = []
    return _load_tracks()


CHARS_PER_SECOND = 15.0
_DEMO_MIN_SPEAK_S = 3.0
_DEMO_MIN_TRACK_S = 5.0


def set_mode(mode: str) -> None:
    global _mode, TIME_SCALE
    _mode = mode
    TIME_SCALE = 1.0 if mode == "realtime" else _DEMO_TIME_SCALE
    logger.info("Mode switched to: %s (TIME_SCALE=%.1f)", _mode, TIME_SCALE)


def get_mode() -> str:
    return _mode


def _sim_sleep(duration_seconds: float) -> float:
    return duration_seconds / TIME_SCALE


def _speaking_duration(text: str) -> float:
    return len(text) / CHARS_PER_SECOND


def _effective_speak_wait(text: str) -> float:
    if not text:
        return 0
    raw = _sim_sleep(_speaking_duration(text))
    if _mode == "realtime":
        return raw
    return max(raw, _DEMO_MIN_SPEAK_S)


def _effective_track_wait(duration_seconds: float) -> float:
    raw = _sim_sleep(duration_seconds)
    if _mode == "realtime":
        return raw
    return max(raw, _DEMO_MIN_TRACK_S)


def _local_time_str() -> str:
    p = get_persona()
    tz = ZoneInfo(p["station"].get("timezone", "Europe/Berlin"))
    return datetime.now(tz).strftime("%H:%M")


def _filter_tracks(
    all_tracks: list[dict],
    recent_ids: list[int],
    last_genres: list[str],
    max_same_genre: int = 2,
) -> list[dict]:
    available = [t for t in all_tracks if t["id"] not in recent_ids]
    if not available:
        available = all_tracks

    if len(last_genres) >= max_same_genre and len(set(last_genres[-max_same_genre:])) == 1:
        same_genre = last_genres[-1]
        filtered = [t for t in available if t["genre"] != same_genre]
        if filtered:
            available = filtered

    return available


async def _pick_track_llm(
    db_conn,
    available_tracks: list[dict],
    phase: str,
    stimuli: list[dict] | None = None,
) -> dict[str, Any] | None:
    system_prompt = build_system_prompt()

    tracks_summary = "\n".join(
        f"  ID {t['id']}: {t['artist']} — {t['title']} ({t['genre']}, {t['duration']}s, Energy: {t['energy']})"
        for t in available_tracks[:20]
    )

    user_msg = f"""Aktuelle Programmphase: {phase}
Aktuelle Uhrzeit: {_local_time_str()}

Verfügbare Tracks:
{tracks_summary}
"""

    if stimuli:
        stimuli_text = "\n".join(
            f"  [{s['category']}] {s['sanitized_text']}" for s in stimuli
        )
        user_msg += f"\nExterne Impulse (für diese Moderation verfügbar):\n{stimuli_text}\n"

    if phase == "impulse" and stimuli:
        user_msg += "\nDu bist im Impuls-Slot — greife mindestens einen externen Impuls in deiner Moderation auf.\n"

    user_msg += "\nWähle einen Track und schreibe deine Moderation. Antworte im JSON-Format."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]

    response = await llm.chat("dj", messages, temperature=0.9)
    if response:
        return llm.parse_json_response(response)
    return None


async def _generate_ad(stimulus: dict) -> dict | None:
    raw = stimulus.get("raw_json")
    if not raw:
        return None

    try:
        briefing = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None

    sponsor = briefing.get("sponsor", "")
    product = briefing.get("product", "")
    key_message = briefing.get("key_message", stimulus.get("sanitized_text", ""))

    system_prompt = build_ad_prompt()
    user_msg = f"Sponsor: {sponsor}\nProdukt: {product}\nKernbotschaft: {key_message}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]

    result = await llm.chat("dj", messages, temperature=0.8, max_tokens=300)
    if result:
        return {
            "text": result.strip(),
            "sponsor": sponsor,
            "product": product,
        }
    return None



async def _generate_station_name(db_conn) -> str:
    p = get_persona()
    station_id = p["station"]["id"]
    prompt = build_naming_prompt()
    messages = [
        {"role": "system", "content": "Du bist ein Radio-Branding-Experte."},
        {"role": "user", "content": prompt},
    ]
    result = await llm.chat("filter", messages, temperature=1.0, max_tokens=30)
    if result:
        name = result.strip().strip('"').strip("'").strip(".")
        await db.set_station_name(db_conn, station_id, name)
        return name
    return station_id.upper()


async def _resolve_station_name(db_conn) -> str | None:
    p = get_persona()
    station_id = p["station"]["id"]
    cfg_name = p["station"].get("name")

    if cfg_name is None:
        set_resolved_name(None)
        return None

    if cfg_name.lower() != "auto":
        set_resolved_name(cfg_name)
        return cfg_name

    existing = await db.get_station_name(db_conn, station_id)
    if existing:
        set_resolved_name(existing)
        return existing

    name = await _generate_station_name(db_conn)
    set_resolved_name(name)
    return name


async def _emit(event: dict) -> None:
    if _broadcast_queue:
        await _broadcast_queue.put(event)


async def run(queue: asyncio.Queue, db_conn, get_listeners=None) -> None:
    global _broadcast_queue, _running, _hour_count
    _broadcast_queue = queue
    _running = True
    _get_listeners = get_listeners or (lambda: 1)

    tracks = get_tracks()
    persona = get_persona()
    rules = persona.get("rules", {})
    no_repeat_hours = rules.get("no_repeat_hours", 4)
    max_same_genre = rules.get("max_same_genre_in_a_row", 2)

    station_name = await _resolve_station_name(db_conn)
    station_id = persona["station"]["id"]

    display = f'"{station_name}"' if station_name else f"[{station_id}]"
    await _emit({
        "station": station_id,
        "type": "system",
        "text": f"Station {display} gestartet. DJ: {persona['dj']['name']}. TIME_SCALE={TIME_SCALE}x",
    })

    while _running:
        _hour_count += 1
        logger.info("=== Sendestunde %d ===", _hour_count)

        for grid_idx, (grid_minute, phase, has_moderation) in enumerate(GRID):
            if not _running:
                break

            has_listeners = _get_listeners() > 0

            recent_ids = await db.get_recent_track_ids(db_conn, no_repeat_hours)
            last_genres = await db.get_last_genres(db_conn, max_same_genre)
            available = _filter_tracks(tracks, recent_ids, last_genres, max_same_genre)

            if has_moderation and has_listeners:
                ad_stimuli = await db.get_pending_stimuli(db_conn, category="ad")
                for ad_stim in ad_stimuli[:1]:
                    ad_result = await _generate_ad(ad_stim)
                    if ad_result:
                        ad_event = {
                            "station": station_id,
                            "type": "ad",
                            "text": ad_result["text"],
                            "sponsor": ad_result["sponsor"],
                        }
                        await _emit(ad_event)
                        await db.log_broadcast(db_conn, "ad", ad_event)
                        await asyncio.sleep(_effective_speak_wait(ad_result["text"]))
                    await db.mark_stimuli_used(db_conn, [ad_stim["id"]])

            stimuli = None
            if phase == "impulse" and has_listeners:
                stimuli = await db.get_pending_stimuli(db_conn, exclude_category="ad")

            decision = None
            if has_moderation and has_listeners:
                decision = await _pick_track_llm(db_conn, available, phase, stimuli)

            track = None
            if decision and decision.get("track_id"):
                track = next((t for t in tracks if t["id"] == decision["track_id"]), None)

            if not track:
                track = random.choice(available)

            moderation_text = decision.get("moderation", "") if decision else ""
            speak_wait = _effective_speak_wait(moderation_text)

            if moderation_text:
                guard_result = streamguard.check(
                    moderation_text,
                    max_chars=persona["dj"].get("max_moderation_chars", 800),
                )

                if guard_result.passed:
                    speak_duration = _speaking_duration(guard_result.text)
                    mod_event = {
                        "station": station_id,
                        "type": "moderation",
                        "text": guard_result.text,
                        "phase": f":{grid_minute:02d} {phase}",
                        "duration": round(speak_duration, 1),
                        "sim_duration": round(speak_wait, 1),
                    }
                    await _emit(mod_event)
                    await db.log_broadcast(db_conn, "moderation", mod_event)

                    for w in guard_result.warnings:
                        await _emit({"station": station_id, "type": "system", "text": f"StreamGuard: {w}"})
                else:
                    sys_event = {
                        "station": station_id,
                        "type": "system",
                        "text": f"StreamGuard: Moderation verworfen ({guard_result.blocked_reason})",
                    }
                    await _emit(sys_event)
                    await db.log_broadcast(db_conn, "guard_block", sys_event)

            if stimuli:
                used_ids = [s["id"] for s in stimuli]
                await db.mark_stimuli_used(db_conn, used_ids)

            if speak_wait > 0.1:
                await asyncio.sleep(speak_wait)

            track_wait = _effective_track_wait(track["duration"])
            now_playing = {
                "station": station_id,
                "type": "now_playing",
                "artist": track["artist"],
                "title": track["title"],
                "genre": track["genre"],
                "duration": track["duration"],
                "sim_duration": round(track_wait, 1),
            }
            await _emit(now_playing)
            await db.log_play(db_conn, track, phase)
            await db.log_broadcast(db_conn, "now_playing", now_playing)

            logger.info(
                ":%02d [%s] %s — %s [speak %.1fs + track %.1fs]",
                grid_minute, phase, track["artist"], track["title"],
                speak_wait, track_wait,
            )
            await asyncio.sleep(track_wait)


def stop() -> None:
    global _running
    _running = False
