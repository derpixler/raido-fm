from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from . import db, dj_agent, llm, sanitizer, stats
from .persona import get_persona, load_persona

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "500"))

_db_conn = None
_broadcast_queue: asyncio.Queue | None = None
_subscribers: list[asyncio.Queue] = []


def _print_startup_summary(station_name: str | None = None) -> None:
    p = get_persona()
    s = p["station"]
    d = p["dj"]
    r = p.get("rules", {})

    dj_cfg = llm._get_role_config("dj")
    filter_cfg = llm._get_role_config("filter")
    fb_url = os.getenv("LLM_FALLBACK_BASE_URL", "")
    fb_model = os.getenv("LLM_FALLBACK_MODEL", "")

    port = os.getenv("PORT", "8080")
    time_scale = os.getenv("TIME_SCALE", "60")
    persona_path = os.getenv("PERSONA_PATH", "persona.yml")
    tracks_file = p.get("tracks_file", "tracks.json")
    tracks_count = len(dj_agent.get_tracks())
    subgenres = ", ".join(s.get("subgenres", []))
    quirks_count = len(d.get("quirks", []))
    forbidden = ", ".join(d.get("forbidden_topics", []))

    def mask(key: str) -> str:
        if not key or len(key) < 8:
            return "***"
        return key[:4] + "..." + key[-4:]

    lines = [
        "",
        "=" * 60,
        "  RAIDO STATION",
        "=" * 60,
        "",
        f"  Persona:        {persona_path}",
        f"  Station ID:     {s['id']}",
        f"  Name:           {station_name or '(wird generiert)'}",
        f"  Genre:          {s['genre']} ({subgenres})",
        f"  Claim:          {s.get('claim', '-')}",
        f"  Zielgruppe:     {s.get('target_audience', '-')}",
        f"  Sprache:        {s.get('language', 'de')}",
        f"  Timezone:       {s.get('timezone', 'Europe/Berlin')}",
        "",
        f"  DJ:             {d['name']}",
        f"  Persoenlichkeit: {d.get('personality', '-')[:60]}...",
        f"  Ton:            {d.get('tone', '-')}",
        f"  Max. Mod.:      {d.get('max_moderation_chars', 800)} Zeichen",
        f"  Quirks:         {quirks_count}",
        f"  Verboten:       {forbidden or '-'}",
        "",
        f"  Tracks:         {tracks_file} ({tracks_count} Tracks)",
        f"  No-Repeat:      {r.get('no_repeat_hours', 4)}h",
        f"  Max. Genre:     {r.get('max_same_genre_in_a_row', 2)}x hintereinander",
        "",
        "  LLM (DJ):       " + dj_cfg["model"],
        f"                  {dj_cfg['base_url']}",
        f"                  Key: {mask(dj_cfg['api_key'])}",
        "  LLM (Filter):   " + filter_cfg["model"],
        f"                  {filter_cfg['base_url']}",
    ]

    if fb_url:
        lines.append(f"  LLM (Fallback): {fb_model}")
        lines.append(f"                  {fb_url}")

    lines += [
        "",
        f"  Port:           {port}",
        f"  TIME_SCALE:     {time_scale}x",
        f"  DB:             {db.DB_PATH}",
        "",
        "-" * 60,
        f"  http://localhost:{port}",
        "-" * 60,
        "",
    ]

    print("\n".join(lines), flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _db_conn, _broadcast_queue
    load_persona()
    persona = get_persona()
    station_id = persona["station"]["id"]

    _db_conn = await db.get_db(station_id)
    _broadcast_queue = asyncio.Queue()

    station_name = await dj_agent._resolve_station_name(_db_conn)
    _print_startup_summary(station_name)

    dj_task = asyncio.create_task(dj_agent.run(_broadcast_queue, _db_conn, lambda: len(_subscribers)))
    fan_task = asyncio.create_task(_fan_out())
    stats_task = asyncio.create_task(_emit_stats_loop())

    yield

    dj_agent.stop()
    stats_task.cancel()
    fan_task.cancel()
    dj_task.cancel()
    if _db_conn:
        await _db_conn.close()


async def _emit_stats_loop():
    await asyncio.sleep(5)
    while True:
        try:
            s = await stats.get_stats(_db_conn, len(_subscribers))
            if _broadcast_queue:
                await _broadcast_queue.put({"type": "stats", **s})
        except Exception:
            pass
        await asyncio.sleep(15)


async def _fan_out():
    while True:
        event = await _broadcast_queue.get()
        dead = []
        for i, q in enumerate(_subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(i)
        for i in reversed(dead):
            _subscribers.pop(i)


app = FastAPI(title="RAIDO Station POC", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="web"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("web/index.html") as f:
        return HTMLResponse(f.read())


@app.get("/stream")
async def stream(request: Request):
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    _subscribers.append(q)

    async def event_generator() -> AsyncGenerator[dict, None]:
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield {"data": json.dumps(event, ensure_ascii=False)}
                except asyncio.TimeoutError:
                    yield {"comment": "keepalive"}
        finally:
            if q in _subscribers:
                _subscribers.remove(q)

    return EventSourceResponse(event_generator())


class InjectRequest(BaseModel):
    category: str
    text: str
    name: str | None = None
    sponsor: str | None = None
    product: str | None = None
    key_message: str | None = None


@app.post("/inject")
async def inject(req: InjectRequest):
    valid_categories = {"news", "listener_comment", "music_request", "ad", "weather"}
    if req.category not in valid_categories:
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"},
        )

    input_len = len(req.text or "")
    if input_len > MAX_INPUT_CHARS:
        return JSONResponse(
            status_code=413,
            content={
                "error": "input_too_long",
                "max_chars": MAX_INPUT_CHARS,
                "actual_chars": input_len,
                "message": f"Max. {MAX_INPUT_CHARS} Zeichen erlaubt.",
            },
        )

    raw_json = None
    text = req.text
    if req.category == "ad":
        ad_data = {"sponsor": req.sponsor, "product": req.product, "key_message": req.key_message}
        raw_json = json.dumps(ad_data, ensure_ascii=False)
        text = req.text or req.key_message or ""

    if req.category == "listener_comment" and req.name:
        text = f"[Hörer: {req.name}] {text}"

    result = await sanitizer.sanitize(
        category=req.category,
        text=text,
        raw_json=raw_json,
        db_conn=_db_conn,
    )

    if _broadcast_queue:
        status = "geflaggt" if result["was_flagged"] else "angenommen"
        await _broadcast_queue.put({
            "station": get_persona()["station"]["id"],
            "type": "system",
            "text": f"Injection [{req.category}]: {status}"
            + (f" — {result['flag_reason']}" if result["was_flagged"] else ""),
        })

    return result


@app.get("/status")
async def status():
    persona = get_persona()
    s = persona["station"]
    d = persona["dj"]
    r = persona.get("rules", {})
    station_name = await db.get_station_name(_db_conn, s["id"]) if _db_conn else None

    dj_cfg = llm._get_role_config("dj")
    filter_cfg = llm._get_role_config("filter")

    return {
        "station": {
            "id": s["id"],
            "name": station_name or s.get("name"),
            "genre": s["genre"],
            "subgenres": s.get("subgenres", []),
            "claim": s.get("claim"),
            "description": s.get("description", "").strip(),
            "lang_definition": s.get("lang_definition", "").strip(),
            "target_audience": s.get("target_audience"),
            "language": s.get("language", "de"),
            "timezone": s.get("timezone", "Europe/Berlin"),
        },
        "dj": {
            "name": d["name"],
            "personality": d.get("personality", "").strip(),
            "tone": d.get("tone", ""),
            "quirks": d.get("quirks", []),
            "max_moderation_chars": d.get("max_moderation_chars", 800),
            "bio": d.get("bio", {}),
        },
        "config": {
            "persona_path": os.getenv("PERSONA_PATH", "persona.yml"),
            "port": os.getenv("PORT", "8080"),
            "time_scale": os.getenv("TIME_SCALE", "60"),
            "tracks_file": persona.get("tracks_file", "tracks.json"),
            "tracks_count": len(dj_agent.get_tracks()),
            "db_path": str(db.DB_PATH),
            "rules": {
                "no_repeat_hours": r.get("no_repeat_hours", 4),
                "max_same_genre_in_a_row": r.get("max_same_genre_in_a_row", 2),
            },
            "llm_dj": {"model": dj_cfg["model"], "base_url": dj_cfg["base_url"]},
            "llm_filter": {"model": filter_cfg["model"], "base_url": filter_cfg["base_url"]},
            "llm_fallback": {
                "model": os.getenv("LLM_FALLBACK_MODEL", ""),
                "base_url": os.getenv("LLM_FALLBACK_BASE_URL", ""),
            },
        },
        "running": dj_agent._running,
    }


@app.get("/stats")
async def get_stats():
    return await stats.get_stats(_db_conn, len(_subscribers))


@app.get("/stats/detail/{category}")
async def stats_detail(category: str):
    if not _db_conn:
        return []

    if category == "tracks":
        cur = await _db_conn.execute(
            "SELECT artist, title, genre, phase, played_at FROM play_history ORDER BY id DESC LIMIT 15"
        )
        return [dict(r) for r in await cur.fetchall()]

    if category == "moderations":
        cur = await _db_conn.execute(
            "SELECT payload, created_at FROM broadcast_log WHERE event_type='moderation' ORDER BY id DESC LIMIT 10"
        )
        rows = await cur.fetchall()
        return [{"text": json.loads(r["payload"]).get("text", "")[:120], "phase": json.loads(r["payload"]).get("phase", ""), "time": r["created_at"]} for r in rows]

    if category == "ads":
        cur = await _db_conn.execute(
            "SELECT payload, created_at FROM broadcast_log WHERE event_type='ad' ORDER BY id DESC LIMIT 10"
        )
        rows = await cur.fetchall()
        return [{"text": json.loads(r["payload"]).get("text", "")[:100], "sponsor": json.loads(r["payload"]).get("sponsor", ""), "time": r["created_at"]} for r in rows]

    if category == "guard":
        cur = await _db_conn.execute(
            "SELECT payload, created_at FROM broadcast_log WHERE event_type='guard_block' ORDER BY id DESC LIMIT 10"
        )
        rows = await cur.fetchall()
        return [{"reason": json.loads(r["payload"]).get("text", ""), "time": r["created_at"]} for r in rows]

    if category == "llm":
        return llm.get_usage()

    if category == "stimuli":
        cur = await _db_conn.execute(
            "SELECT category, sanitized_text, sanitized_at, was_flagged, flag_reason FROM external_stimuli ORDER BY id DESC LIMIT 10"
        )
        return [dict(r) for r in await cur.fetchall()]

    if category == "flagged":
        cur = await _db_conn.execute(
            "SELECT category, raw_text, flag_reason, sanitized_at FROM external_stimuli WHERE was_flagged=1 ORDER BY id DESC LIMIT 10"
        )
        return [dict(r) for r in await cur.fetchall()]

    return []


@app.get("/mode")
async def get_mode():
    return {"mode": dj_agent.get_mode(), "time_scale": dj_agent.TIME_SCALE}


@app.post("/mode/{mode}")
async def set_mode(mode: str):
    if mode not in ("realtime", "demo"):
        return JSONResponse(status_code=400, content={"error": "Mode must be 'realtime' or 'demo'"})
    dj_agent.set_mode(mode)
    return {"mode": mode, "time_scale": dj_agent.TIME_SCALE}


@app.post("/reset")
async def reset(regenerate_name: bool = False):
    persona = get_persona()
    station_id = persona["station"]["id"]

    if _db_conn:
        await db.reset_db(_db_conn, regenerate_name=regenerate_name, station_id=station_id)

    load_persona()
    llm.reset_clients()
    llm.reset_usage()

    if regenerate_name and _db_conn:
        new_name = await dj_agent._generate_station_name(_db_conn)
        return {"status": "reset", "new_name": new_name}

    return {"status": "reset"}
