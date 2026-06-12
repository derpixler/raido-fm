from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

import httpx
import yaml
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import db, docker_mgr, persona_generator, ad_generator, content_generator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "raido-admin")
MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "500"))
MAX_STATIONS = int(os.getenv("MAX_STATIONS", "5"))
MAX_PERSONAS = int(os.getenv("MAX_PERSONAS", "20"))

_db = None


def _global_env() -> dict:
    keys = [
        "LLM_DJ_BASE_URL", "LLM_DJ_MODEL", "LLM_DJ_API_KEY",
        "LLM_FILTER_BASE_URL", "LLM_FILTER_MODEL", "LLM_FILTER_API_KEY",
        "LLM_FALLBACK_BASE_URL", "LLM_FALLBACK_MODEL", "LLM_FALLBACK_API_KEY",
        "TIME_SCALE", "MAX_INPUT_CHARS",
    ]
    return {k: os.getenv(k, "") for k in keys}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _db
    _db = await db.get_db()
    docker_mgr.set_db(_db)

    cleanup_task = asyncio.create_task(docker_mgr.auto_cleanup_loop())
    poll_task = asyncio.create_task(_poll_injection_status())

    print("\n" + "=" * 50, flush=True)
    print("  RAIDO HUB", flush=True)
    print("=" * 50, flush=True)
    print(f"  Admin-Token: {ADMIN_TOKEN[:4]}...", flush=True)
    print(f"  Station-Image: {docker_mgr.STATION_IMAGE}", flush=True)
    print(f"  Port-Range: {docker_mgr.PORT_RANGE_START}-{docker_mgr.PORT_RANGE_END}", flush=True)
    print(f"  Idle-Timeout: {docker_mgr.IDLE_TIMEOUT_S // 60}min", flush=True)
    print(f"  Max-Input-Chars: {MAX_INPUT_CHARS}", flush=True)
    print("=" * 50 + "\n", flush=True)

    yield

    poll_task.cancel()
    cleanup_task.cancel()
    if _db:
        await _db.close()


app = FastAPI(title="RAIDO Hub", lifespan=lifespan)


async def _poll_injection_status():
    await asyncio.sleep(30)
    while True:
        try:
            if not _db:
                await asyncio.sleep(60)
                continue
            pending = await db.get_pending_injections(_db)
            if not pending:
                await asyncio.sleep(60)
                continue

            stations = await docker_mgr.discover_stations()

            for inj in pending:
                slug = inj.get("station_slug")
                station = next((s for s in stations if s.get("slug") == slug), None)
                if not station or not station.get("station_status"):
                    continue

                port = station.get("port")

                async with httpx.AsyncClient(timeout=5.0) as http:
                    try:
                        resp = await http.get(f"http://host.docker.internal:{port}/stats/detail/stimuli")
                        if resp.status_code != 200:
                            continue
                        stimuli = resp.json()
                        if not isinstance(stimuli, list):
                            continue
                    except Exception:
                        continue

                sid = inj.get("stimulus_id")
                content = (inj.get("content") or "")[:50].lower().strip()
                matched = False

                for stim in stimuli:
                    # Match by stimulus_id OR by similar content
                    if sid and stim.get("id") == sid:
                        matched = True
                    elif not sid and content and content in (stim.get("sanitized_text") or "").lower():
                        matched = True

                    if matched:
                        was_flagged = stim.get("was_flagged", 0)
                        if was_flagged:
                            await db.update_injection_status(_db, inj["id"], "flagged",
                                flagged=True, flag_reason=stim.get("flag_reason"))
                        elif stim.get("used_at"):
                            await db.update_injection_status(_db, inj["id"], "used",
                                moderation_text=stim.get("sanitized_text"))
                        else:
                            # Still pending at the station level, keep checking
                            pass
                        break

                if not matched:
                    # Check if injection is older than 30 min → timeout
                    injected = inj.get("injected_at", "")
                    if injected:
                        elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(injected)).total_seconds()
                        if elapsed > 1800:
                            await db.update_injection_status(_db, inj["id"], "timeout")
        except Exception:
            pass
        await asyncio.sleep(60)
app.mount("/static", StaticFiles(directory="web"), name="static")


def require_admin(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token != ADMIN_TOKEN:
        raise HTTPException(401, "Admin token required")


@app.get("/", response_class=HTMLResponse)
async def landing():
    with open("web/index.html") as f:
        return HTMLResponse(f.read())


@app.get("/stations")
async def list_stations():
    return await docker_mgr.discover_stations()


class CreateStationRequest(BaseModel):
    persona_yaml: str
    tracks_json: str | None = None
    station_id: str | None = None


@app.post("/stations")
async def create_station(req: CreateStationRequest):
    stations = await docker_mgr.discover_stations()
    running = [s for s in stations if s["status"] == "running"]
    if len(running) >= MAX_STATIONS:
        return JSONResponse({"error": f"Max. {MAX_STATIONS} laufende Stationen erlaubt ({len(running)} aktiv)"}, status_code=429)

    try:
        parsed = yaml.safe_load(req.persona_yaml)
    except yaml.YAMLError as e:
        return JSONResponse({"error": f"Invalid YAML: {e}"}, status_code=400)

    if "station" not in parsed or "dj" not in parsed:
        return JSONResponse({"error": "YAML must contain 'station' and 'dj' sections"}, status_code=400)

    validation = await persona_generator.validate_persona(req.persona_yaml)
    if not validation["valid"]:
        return JSONResponse({"error": "Persona validation failed", "issues": validation["issues"]}, status_code=422)

    station_id = req.station_id or parsed["station"].get("id", "generated")
    slug = persona_generator._slugify(
        parsed["station"].get("id", station_id)
    )

    tracks = req.tracks_json
    if not tracks:
        genre = parsed["station"].get("genre", "")
        subgenres = parsed["station"].get("subgenres", [])
        tracks = await persona_generator.generate_tracks(genre, subgenres)
        if not tracks:
            return JSONResponse({"error": "Track generation failed"}, status_code=500)

    parsed["tracks_file"] = f"tracks_{station_id}.json"
    final_yaml = yaml.dump(parsed, allow_unicode=True, default_flow_style=False)

    result = await docker_mgr.create_station(station_id, slug, final_yaml, tracks, _global_env())
    return result


@app.delete("/stations/{station_id}", dependencies=[Depends(require_admin)])
async def delete_station(station_id: str):
    success = await docker_mgr.stop_station(station_id)
    if not success:
        raise HTTPException(400, "Cannot stop station (last one or protected)")
    return {"status": "stopped", "station_id": station_id}


@app.post("/admin/drop-ad", dependencies=[Depends(require_admin)])
async def drop_random_ad():
    stations = await docker_mgr.discover_stations()
    live = [s for s in stations if s["status"] == "running"]
    if not live:
        raise HTTPException(400, "No running stations available")

    target = random.choice(live)
    status = target.get("station_status", {})
    genre = status.get("station", {}).get("genre", "radio")
    audience = status.get("station", {}).get("target_audience", "alle")

    ad = await ad_generator.generate_random_ad(genre, audience)

    port = target["port"]
    async with httpx.AsyncClient(timeout=10.0) as http:
        resp = await http.post(
            f"http://host.docker.internal:{port}/inject",
            json={"category": "ad", "text": "", "sponsor": ad["sponsor"], "product": ad["product"], "key_message": ad["key_message"]},
        )

    if _db:
        await db.log_ad(_db, target["slug"], ad["sponsor"], ad["product"], ad["key_message"])

    return {"station": target["slug"], "ad": ad, "status": resp.status_code}


async def _drop_content(category: str) -> dict:
    stations = await docker_mgr.discover_stations()
    live = [s for s in stations if s["status"] == "running"]
    if not live:
        raise HTTPException(400, "No running stations available")

    target = random.choice(live)
    status = target.get("station_status", {})
    genre = status.get("station", {}).get("genre", "radio")

    text = await content_generator.generate_content(category, genre)

    port = target["port"]
    payload = {"category": category, "text": text}
    if category == "listener_comment":
        payload["name"] = text.split("[")[1].split("]")[0] if "[" in text else "Hoerer"

    stimulus_id = None
    async with httpx.AsyncClient(timeout=10.0) as http:
        resp = await http.post(f"http://host.docker.internal:{port}/inject", json=payload)
        try:
            resp_data = resp.json()
            stimulus_id = resp_data.get("id")
        except Exception:
            pass

    if _db:
        await db.log_injection(_db, target["slug"], port, category, text, stimulus_id)
        await db.cleanup_old_entries(_db, "injection_log", category)

    return {"station": target["slug"], "category": category, "text": text, "stimulus_id": stimulus_id}


@app.post("/admin/drop-news", dependencies=[Depends(require_admin)])
async def drop_news():
    return await _drop_content("news")

@app.post("/admin/drop-weather", dependencies=[Depends(require_admin)])
async def drop_weather():
    return await _drop_content("weather")

@app.post("/admin/drop-comment", dependencies=[Depends(require_admin)])
async def drop_comment():
    return await _drop_content("listener_comment")

@app.post("/admin/drop-request", dependencies=[Depends(require_admin)])
async def drop_request():
    return await _drop_content("music_request")


@app.post("/stations/from-persona/{persona_id}")
async def start_from_persona(persona_id: int):
    stations = await docker_mgr.discover_stations()
    running = [s for s in stations if s["status"] == "running"]
    if len(running) >= MAX_STATIONS:
        return JSONResponse({"error": f"Max. {MAX_STATIONS} laufende Stationen erlaubt ({len(running)} aktiv)"}, status_code=429)

    persona = await db.get_persona_by_id(_db, persona_id)
    if not persona:
        raise HTTPException(404, "Persona not found")

    validation = await persona_generator.validate_persona(persona["persona_yaml"])
    if not validation["valid"]:
        return JSONResponse({"error": "Persona enthaelt unzulaessige Inhalte", "issues": validation["issues"]}, status_code=422)

    parsed = yaml.safe_load(persona["persona_yaml"])
    station_id = parsed["station"].get("id", "relaunch")
    slug = persona["slug"]

    tracks = persona.get("tracks_json")
    if not tracks:
        genre = parsed["station"].get("genre", "")
        subgenres = parsed["station"].get("subgenres", [])
        tracks = await persona_generator.generate_tracks(genre, subgenres)
        if not tracks:
            return JSONResponse({"error": "Track generation failed"}, status_code=500)

    parsed["tracks_file"] = f"tracks_{station_id}.json"
    final_yaml = yaml.dump(parsed, allow_unicode=True, default_flow_style=False)

    result = await docker_mgr.create_station(station_id, slug, final_yaml, tracks, _global_env())
    return result


class GenerateRequest(BaseModel):
    genre_hint: str | None = None
    language: str = "de"


@app.post("/generate-persona")
async def generate_persona(req: GenerateRequest = None):
    persona_count = await db.count_personas(_db)
    if persona_count >= MAX_PERSONAS:
        return JSONResponse({"error": f"Max. {MAX_PERSONAS} gespeicherte Personas erlaubt ({persona_count} vorhanden)"}, status_code=429)

    hint = req.genre_hint if req else None
    lang = req.language if req else "de"
    result = await persona_generator.generate_persona(hint, lang)
    if "error" in result:
        return JSONResponse(result, status_code=500)

    validation = await persona_generator.validate_persona(result.get("persona_yaml", ""))
    if not validation["valid"]:
        return JSONResponse({"error": "Generierte Persona enthaelt unzulaessige Inhalte. Bitte neu generieren.", "issues": validation["issues"]}, status_code=422)

    genre = result.get("parsed", {}).get("station", {}).get("genre", "")
    subgenres = result.get("parsed", {}).get("station", {}).get("subgenres", [])
    tracks = await persona_generator.generate_tracks(genre, subgenres)

    result["tracks_json"] = tracks
    return result


@app.get("/help.md")
async def help_md():
    with open("web/help.md") as f:
        return f.read()


@app.get("/help", response_class=HTMLResponse)
async def help_page():
    with open("web/help.md") as f:
        content = f.read()
    html = _md_to_html(content)
    return HTMLResponse(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>RAIDO — Hilfe</title>
<style>
body{{font-family:'SF Mono','Fira Code',monospace;background:#0a0a0a;color:#bbb;padding:24px 32px;max-width:640px;margin:0 auto;line-height:1.6;font-size:13px}}
h1{{color:#fff;font-size:18px;margin-bottom:16px}}
h2{{color:#ccc;font-size:14px;margin:24px 0 8px;border-bottom:1px solid #1a1a1a;padding-bottom:4px}}
h3{{color:#999;font-size:12px;margin:16px 0 4px}}
p{{margin:6px 0}}
code{{background:#111;padding:1px 6px;border-radius:3px;color:#4ade80;font-size:12px}}
blockquote{{border-left:2px solid #333;margin:8px 0;padding-left:12px;color:#888;font-style:italic}}
strong{{color:#e0e0e0}}
li{{margin:4px 0;padding-left:4px}}
</style></head><body>{html}</body></html>""")


def _md_to_html(text: str) -> str:
    lines = text.split('\n')
    result = []
    in_list = False
    for line in lines:
        if line.startswith('# '):
            if in_list: result.append('</ul>'); in_list = False
            result.append(f'<h1>{line[2:]}</h1>')
        elif line.startswith('## '):
            if in_list: result.append('</ul>'); in_list = False
            result.append(f'<h2>{line[3:]}</h2>')
        elif line.startswith('> '):
            result.append(f'<blockquote>{line[2:]}</blockquote>')
        elif line.startswith('- '):
            if not in_list: result.append('<ul>'); in_list = True
            result.append(f'<li>{line[2:]}</li>')
        elif in_list and not line.startswith('- ') and line.strip():
            result.append('</ul>'); in_list = False
        elif line == '---':
            result.append('<hr style="border-color:#1a1a1a;margin:16px 0">')
        elif line.startswith('```'):
            continue
        elif line.startswith('**'):
            result.append(f'<strong>{line.strip(" *")}</strong></br>')
        elif line.strip():
            result.append(f'<p>{line}</p>')
    if in_list: result.append('</ul>')
    return '\n'.join(result)


@app.get("/personas")
async def list_personas():
    return await db.get_personas(_db)


@app.get("/ads")
async def list_ads():
    return await db.get_ads(_db) if _db else []


@app.get("/injections")
async def list_injections():
    return await db.get_visible_injections(_db) if _db else []


@app.delete("/personas/{persona_id}", dependencies=[Depends(require_admin)])
async def delete_persona(persona_id: int):
    deleted = await db.delete_persona(_db, persona_id)
    if not deleted:
        raise HTTPException(404, "Persona not found")
    return {"status": "deleted", "id": persona_id}


@app.get("/overview")
async def overview():
    stations = await docker_mgr.discover_stations()
    running = [s for s in stations if s["status"] == "running"]

    total_tracks = 0
    total_listeners = 0
    total_llm_calls = 0
    total_tokens_in = 0
    total_tokens_out = 0

    for s in running:
        stats = s.get("stats", {})
        total_tracks += stats.get("tracks", {}).get("played", 0)
        total_listeners += stats.get("subscribers", 0)
        llm_data = stats.get("llm", {})
        total_llm_calls += llm_data.get("calls", 0)
        total_tokens_in += llm_data.get("tokens_in", 0)
        total_tokens_out += llm_data.get("tokens_out", 0)

    persona_count = await db.count_personas(_db)

    return {
        "stations_running": len(running),
        "stations_total": len(stations),
        "max_stations": MAX_STATIONS,
        "personas_count": persona_count,
        "max_personas": MAX_PERSONAS,
        "total_listeners": total_listeners,
        "total_tracks_played": total_tracks,
        "total_llm_calls": total_llm_calls,
        "total_tokens_in": total_tokens_in,
        "total_tokens_out": total_tokens_out,
    }


@app.api_route("/s/{slug}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_station(slug: str, path: str, request: Request):
    stations = await docker_mgr.discover_stations()
    station = next((s for s in stations if s["slug"] == slug), None)
    if not station:
        raise HTTPException(404, f"Station '{slug}' not found")

    port = station["port"]
    target_url = f"http://host.docker.internal:{port}/{path}"

    if path == "stream":
        return await _proxy_sse(target_url)

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(
            method=request.method,
            url=target_url,
            headers={k: v for k, v in request.headers.items() if k.lower() not in ("host", "connection")},
            content=await request.body(),
        )

    return JSONResponse(
        status_code=resp.status_code,
        content=resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"raw": resp.text},
        headers={"access-control-allow-origin": "*"},
    )


@app.get("/s/{slug}/")
async def proxy_station_root(slug: str):
    stations = await docker_mgr.discover_stations()
    station = next((s for s in stations if s["slug"] == slug), None)
    if not station:
        raise HTTPException(404, f"Station '{slug}' not found")

    port = station["port"]
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"http://host.docker.internal:{port}/")
    return HTMLResponse(resp.text)


async def _proxy_sse(target_url: str):
    async def stream():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", target_url) as resp:
                async for line in resp.aiter_lines():
                    yield line + "\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "cache-control": "no-cache",
            "connection": "keep-alive",
            "access-control-allow-origin": "*",
        },
    )
