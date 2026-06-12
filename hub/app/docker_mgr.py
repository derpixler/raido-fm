from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import docker
import httpx

from . import db as hub_db

logger = logging.getLogger(__name__)

STATION_IMAGE = os.getenv("STATION_IMAGE", "raido-station:latest")
PERSONAS_DIR = Path("/app/personas")
PERSONAS_HOST_PATH = os.getenv("PERSONAS_HOST_PATH", str(PERSONAS_DIR))
STATIONS_DATA_HOST_PATH = os.getenv(
    "STATIONS_DATA_HOST_PATH",
    os.path.join(os.path.dirname(PERSONAS_HOST_PATH), "stations-data"),
)
PORT_RANGE_START = 8081
PORT_RANGE_END = 8099
IDLE_TIMEOUT_S = 2700

_client: docker.DockerClient | None = None
_db = None


def get_docker() -> docker.DockerClient:
    global _client
    if _client is None:
        _client = docker.from_env()
    return _client


def set_db(db_conn):
    global _db
    _db = db_conn


def _slugify(name: str) -> str:
    import re
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s or "station"


async def discover_stations() -> list[dict]:
    client = get_docker()
    containers = client.containers.list(filters={"label": "raido.role=station"})
    stations = []

    for c in containers:
        station_id = c.labels.get("raido.station.id", c.name)
        slug = c.labels.get("raido.station.slug", station_id)
        port = c.labels.get("raido.station.port", "8080")
        protected = c.labels.get("raido.station.protected", "false") == "true"

        info = {
            "station_id": station_id,
            "slug": slug,
            "port": int(port),
            "container_name": c.name,
            "status": c.status,
            "protected": protected,
        }

        try:
            async with httpx.AsyncClient(timeout=3.0) as http:
                resp = await http.get(f"http://host.docker.internal:{port}/status")
                if resp.status_code == 200:
                    info["station_status"] = resp.json()
                resp2 = await http.get(f"http://host.docker.internal:{port}/stats")
                if resp2.status_code == 200:
                    stats = resp2.json()
                    info["subscribers"] = stats.get("subscribers", 0)
                    info["stats"] = stats
        except Exception:
            info["station_status"] = None
            info["subscribers"] = 0

        if _db and info["subscribers"] == 0:
            reg = await hub_db.get_station_by_slug(_db, slug)
            if reg and reg.get("idle_since"):
                info["idle_since"] = reg["idle_since"]

        stations.append(info)

    return stations


def _get_used_ports() -> set[int]:
    client = get_docker()
    used = set()
    containers = client.containers.list(filters={"label": "raido.role=station"})
    for c in containers:
        port_str = c.labels.get("raido.station.port")
        if port_str:
            used.add(int(port_str))
    return used


def find_free_port() -> int:
    used = _get_used_ports()
    for port in range(PORT_RANGE_START, PORT_RANGE_END + 1):
        if port not in used:
            return port
    raise RuntimeError("No free ports available")


async def create_station(station_id: str, slug: str, persona_yaml: str, tracks_json: str, global_env: dict) -> dict:
    client = get_docker()
    port = find_free_port()

    persona_path = PERSONAS_DIR / f"{station_id}.yml"
    tracks_path = PERSONAS_DIR / f"tracks_{station_id}.json"
    env_path = PERSONAS_DIR / f"{station_id}.env"

    persona_path.write_text(persona_yaml)
    tracks_path.write_text(tracks_json)
    env_path.write_text(f"PORT=8080\nPERSONA_PATH=/app/personas/{station_id}.yml\nSTATION_ID={station_id}\n")

    environment = {
        "PORT": str(port),
        "PERSONA_PATH": f"/app/personas/{station_id}.yml",
        "STATION_ID": station_id,
        "TIME_SCALE": global_env.get("TIME_SCALE", "60"),
        "LLM_DJ_BASE_URL": global_env.get("LLM_DJ_BASE_URL", ""),
        "LLM_DJ_MODEL": global_env.get("LLM_DJ_MODEL", ""),
        "LLM_DJ_API_KEY": global_env.get("LLM_DJ_API_KEY", ""),
        "LLM_FILTER_BASE_URL": global_env.get("LLM_FILTER_BASE_URL", ""),
        "LLM_FILTER_MODEL": global_env.get("LLM_FILTER_MODEL", ""),
        "LLM_FILTER_API_KEY": global_env.get("LLM_FILTER_API_KEY", ""),
        "LLM_FALLBACK_BASE_URL": global_env.get("LLM_FALLBACK_BASE_URL", ""),
        "LLM_FALLBACK_MODEL": global_env.get("LLM_FALLBACK_MODEL", ""),
        "LLM_FALLBACK_API_KEY": global_env.get("LLM_FALLBACK_API_KEY", ""),
        "MAX_INPUT_CHARS": global_env.get("MAX_INPUT_CHARS", "500"),
        "DB_DIR": "/app/data",
    }

    container_name = f"raido-{station_id}"

    try:
        old = client.containers.get(container_name)
        old.remove(force=True)
    except docker.errors.NotFound:
        pass

    station_data_host = os.path.join(STATIONS_DATA_HOST_PATH, station_id)

    container = client.containers.run(
        image=STATION_IMAGE,
        name=container_name,
        detach=True,
        ports={f"{port}/tcp": port},
        volumes={
            PERSONAS_HOST_PATH: {"bind": "/app/personas", "mode": "ro"},
            os.path.join(os.path.dirname(PERSONAS_HOST_PATH), "contributors.yml"): {"bind": "/app/contributors.yml", "mode": "ro"},
            station_data_host: {"bind": "/app/data", "mode": "rw"},
        },
        environment=environment,
        labels={
            "raido.role": "station",
            "raido.station.id": station_id,
            "raido.station.slug": slug,
            "raido.station.port": str(port),
            "raido.station.protected": "false",
        },
    )

    if _db:
        await hub_db.register_station(_db, station_id, slug, port, container_name)
        await hub_db.save_persona(_db, station_id, slug, persona_yaml, tracks_json)

    logger.info("Station created: %s (slug=%s, port=%d)", station_id, slug, port)
    return {"station_id": station_id, "slug": slug, "port": port, "container": container_name}


async def stop_station(station_id: str) -> bool:
    client = get_docker()
    stations = await discover_stations()
    running = [s for s in stations if s["status"] == "running"]

    if len(running) <= 1:
        logger.warning("Cannot stop last running station")
        return False

    target = next((s for s in stations if s["station_id"] == station_id), None)
    if not target:
        return False

    if target.get("protected"):
        logger.warning("Cannot stop protected station: %s", station_id)
        return False

    try:
        container = client.containers.get(target["container_name"])
        container.stop(timeout=10)
        container.remove()
    except Exception as e:
        logger.error("Failed to stop station %s: %s", station_id, e)
        return False

    if _db:
        await hub_db.unregister_station(_db, station_id)

    logger.info("Station stopped: %s", station_id)
    return True


async def auto_cleanup_loop():
    while True:
        await asyncio.sleep(300)
        try:
            stations = await discover_stations()
            running = [s for s in stations if s["status"] == "running"]

            for station in running:
                if station.get("protected"):
                    continue

                listeners = station.get("subscribers", 0)
                sid = station["station_id"]

                if listeners == 0:
                    if _db:
                        reg = await hub_db.get_station_by_slug(_db, station["slug"])
                        if reg and not reg.get("idle_since"):
                            await hub_db.set_idle_since(_db, sid, datetime.now(timezone.utc).isoformat())
                        elif reg and reg.get("idle_since"):
                            idle_start = datetime.fromisoformat(reg["idle_since"])
                            elapsed = (datetime.now(timezone.utc) - idle_start).total_seconds()
                            if elapsed > IDLE_TIMEOUT_S and len(running) > 1:
                                logger.info("Auto-stopping idle station: %s (idle %.0fs)", sid, elapsed)
                                await stop_station(sid)
                else:
                    if _db:
                        await hub_db.set_idle_since(_db, sid, None)
        except Exception as e:
            logger.warning("Auto-cleanup error: %s", e)
