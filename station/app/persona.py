from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Any

from .md_loader import load_prompt

PERSONA_PATH = Path(os.getenv("PERSONA_PATH", "persona.yml"))

_persona: dict[str, Any] | None = None


def load_persona(path: Path | None = None) -> dict[str, Any]:
    global _persona
    p = path or PERSONA_PATH
    with open(p) as f:
        data = yaml.safe_load(f)

    if env_name := os.getenv("STATION_NAME"):
        data["station"]["name"] = env_name
    if env_genre := os.getenv("STATION_GENRE"):
        data["station"]["genre"] = env_genre
    if env_personality := os.getenv("DJ_PERSONALITY"):
        data["dj"]["personality"] = env_personality

    _persona = data
    return data


def get_persona() -> dict[str, Any]:
    if _persona is None:
        return load_persona()
    return _persona


def build_system_prompt() -> str:
    p = get_persona()
    station = p["station"]
    dj = p["dj"]
    rules = p.get("rules", {})
    grid = p.get("program_grid", {})

    lang = station.get("language", "de")

    quirks_text = "\n".join(f"  - {q}" for q in dj.get("quirks", []))
    forbidden = ", ".join(dj.get("forbidden_topics", []))
    subgenres = ", ".join(station.get("subgenres", []))

    station_name = station.get("_resolved_name")
    name_line = f' on the station "{station_name}"' if station_name else ""
    en_name_line = f' on the station "{station_name}"' if station_name else ""

    if lang == "en":
        return load_prompt("dj/dj_system_en.md").format(
            name=dj["name"],
            name_line=en_name_line,
            claim=station.get("claim", ""),
            positioning=station.get("description", "").strip(),
            genre=station["genre"],
            subgenres=subgenres,
            audience=station.get("target_audience", ""),
            timezone=station.get("timezone", "Europe/Berlin"),
            personality=dj["personality"],
            tone=dj["tone"],
            max_chars=dj.get("max_moderation_chars", 800),
            quirks=quirks_text,
            no_repeat=rules.get("no_repeat_hours", 4),
            max_genre=rules.get("max_same_genre_in_a_row", 2),
            impulse_minute=grid.get("impulse_slot_minute", 30),
            forbidden=forbidden,
        )

    return load_prompt("dj/dj_system_de.md").format(
        name=dj["name"],
        name_line=name_line,
        claim=station.get("claim", ""),
        positioning=station.get("description", "").strip(),
        genre=station["genre"],
        subgenres=subgenres,
        audience=station.get("target_audience", ""),
        timezone=station.get("timezone", "Europe/Berlin"),
        personality=dj["personality"],
        tone=dj["tone"],
        max_chars=dj.get("max_moderation_chars", 800),
        quirks=quirks_text,
        no_repeat=rules.get("no_repeat_hours", 4),
        max_genre=rules.get("max_same_genre_in_a_row", 2),
        impulse_minute=grid.get("impulse_slot_minute", 30),
        forbidden=forbidden,
    )


def set_resolved_name(name: str | None) -> None:
    p = get_persona()
    if name:
        p["station"]["_resolved_name"] = name
    else:
        p["station"].pop("_resolved_name", None)


def build_naming_prompt() -> str:
    p = get_persona()
    station = p["station"]
    subgenres = ", ".join(station.get("subgenres", []))
    lang = station.get("language", "de")

    return load_prompt("dj/naming.md").format(
        genre=station["genre"],
        subgenres=subgenres,
        positioning=station.get("description", "").strip(),
        audience=station.get("target_audience", ""),
        claim=station.get("claim", ""),
        language=lang,
    )


def build_ad_prompt() -> str:
    p = get_persona()
    dj = p["dj"]
    lang = p["station"].get("language", "de")

    if lang == "en":
        return load_prompt("dj/ad_reading_en.md").format(
            name=dj["name"],
            personality=dj["personality"],
            tone=dj["tone"],
        )

    return load_prompt("dj/ad_reading_de.md").format(
        name=dj["name"],
        personality=dj["personality"],
        tone=dj["tone"],
    )
