from __future__ import annotations

import json
import logging
import re

import yaml

from . import llm
from .md_loader import load_prompt

logger = logging.getLogger(__name__)

PERSONA_SCHEMA = load_prompt("persona/persona_schema.md")
PERSONA_PROMPT = load_prompt("persona/persona_system.md").format(schema=PERSONA_SCHEMA)
TRACKS_PROMPT = load_prompt("persona/persona_tracks.md")
STATION_SECTION_PROMPT = load_prompt("persona/station_section.md")
DJ_SECTION_PROMPT = load_prompt("persona/dj_section.md")
_STATION_SCHEMA_YAML = load_prompt("persona/station_schema.md")
_DJ_SCHEMA_YAML = load_prompt("persona/dj_schema.md")
CONTENT_SAFETY_PROMPT = load_prompt("persona/content_safety.md")


async def generate_persona(genre_hint: str | None = None, language: str = "de", dj_hint: str | None = None) -> dict:
    prompt = PERSONA_PROMPT
    if genre_hint:
        prompt += f'\n\nGenre hint from user: "{genre_hint}" — use it as inspiration, but be creative.'
    if dj_hint:
        prompt += f'\n\nDJ hint from user: "{dj_hint}" — use it as inspiration for the DJ character, but be creative.'
    if language != "de":
        prompt += f'\n\nLANGUAGE: The entire persona must be in language "{language}" — station, DJ name, bio, quirks, everything.'
    prompt += '\n\nIMPORTANT: The station language must be "' + language + '".'

    messages = [
        {"role": "system", "content": "You are a creative radio station architect."},
        {"role": "user", "content": prompt},
    ]

    result = await llm.chat("filter", messages, temperature=1.1, max_tokens=2000)
    if not result:
        return {"error": "LLM call failed"}

    clean = result.strip()
    clean = re.sub(r"^```ya?ml\s*", "", clean)
    clean = re.sub(r"\s*```$", "", clean)
    clean = re.sub(r",\s*\]", "]", clean)

    try:
        parsed = yaml.safe_load(clean)
        if not parsed or "station" not in parsed or "dj" not in parsed:
            return {"error": "Invalid YAML structure", "raw": clean}

        station_id = parsed["station"].get("id", "generated")
        return {"persona_yaml": clean, "parsed": parsed, "station_id": station_id}
    except yaml.YAMLError as e:
        return {"error": f"YAML parse error: {e}", "raw": clean}


async def generate_tracks(genre: str, subgenres: list[str]) -> str | None:
    prompt = TRACKS_PROMPT.format(genre=genre, subgenres=", ".join(subgenres))

    messages = [
        {"role": "system", "content": "You are a music curator and track library expert."},
        {"role": "user", "content": prompt},
    ]

    result = await llm.chat("filter", messages, temperature=0.8, max_tokens=4000)
    if not result:
        return None

    clean = result.strip()
    clean = re.sub(r"^```json?\s*", "", clean)
    clean = re.sub(r"\s*```$", "", clean)

    try:
        tracks = json.loads(clean)
        if isinstance(tracks, list) and len(tracks) > 0:
            for i, t in enumerate(tracks):
                t["id"] = i + 1
            return json.dumps(tracks, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        pass

    return clean


async def generate_station_section(genre_hint: str | None = None, language: str = "de") -> dict:
    hint = ""
    if genre_hint:
        hint = f'Genre hint from user: "{genre_hint}" — use it as inspiration, but be creative.'
    if language != "de":
        hint += f'\n\nLANGUAGE: The station must be in language "{language}".'
    hint += '\n\nIMPORTANT: The station language must be "' + language + '".'

    prompt = STATION_SECTION_PROMPT.format(station_hint=hint, station_schema=_STATION_SCHEMA_YAML)

    messages = [
        {"role": "system", "content": "You are a creative radio station architect."},
        {"role": "user", "content": prompt},
    ]

    result = await llm.chat("filter", messages, temperature=1.0, max_tokens=800)
    if not result:
        return {"error": "LLM call failed"}

    clean = result.strip()
    clean = re.sub(r"^```ya?ml\s*", "", clean)
    clean = re.sub(r"\s*```$", "", clean)
    clean = re.sub(r",\s*\]", "]", clean)

    try:
        parsed = yaml.safe_load(clean)
        if not parsed or "station" not in parsed:
            return {"error": "Invalid station YAML structure", "raw": clean}
        station_id = parsed["station"].get("id", "generated")
        return {"persona_yaml": clean, "parsed": parsed, "station_id": station_id}
    except yaml.YAMLError as e:
        return {"error": f"YAML parse error: {e}", "raw": clean}


async def generate_dj_section(traits_hint: str | None = None, station_context: str | None = None) -> dict:
    hint = ""
    if traits_hint:
        hint = f'DJ traits from user: "{traits_hint}" — use it as inspiration, but be creative.'

    ctx = station_context or "no station context available"

    prompt = DJ_SECTION_PROMPT.format(dj_hint=hint, station_context=ctx, dj_schema=_DJ_SCHEMA_YAML)

    messages = [
        {"role": "system", "content": "You are a creative radio character designer."},
        {"role": "user", "content": prompt},
    ]

    result = await llm.chat("filter", messages, temperature=1.1, max_tokens=1000)
    if not result:
        return {"error": "LLM call failed"}

    clean = result.strip()
    clean = re.sub(r"^```ya?ml\s*", "", clean)
    clean = re.sub(r"\s*```$", "", clean)
    clean = re.sub(r",\s*\]", "]", clean)

    try:
        parsed = yaml.safe_load(clean)
        if not parsed or "dj" not in parsed:
            return {"error": "Invalid DJ YAML structure", "raw": clean}
        return {"persona_yaml": clean, "parsed": parsed}
    except yaml.YAMLError as e:
        return {"error": f"YAML parse error: {e}", "raw": clean}


def extract_slug(persona_yaml: str) -> str:
    try:
        parsed = yaml.safe_load(persona_yaml)
        name = parsed.get("station", {}).get("id", "station")
        return _slugify(name)
    except Exception:
        return "station"


def _slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "station"


HARD_CONTENT_FILTER = [
    r"nazi", r"nsdap", r"hitler", r"holocaust", r"sieg\s*heil",
    r"white\s*power", r"racial\s*doctrine", r"genocide",
    r"child\s*porn", r"pedophil",
    r"attack\s*plan", r"bomb\s*making", r"contract\s*killing",
    r"isis", r"al.qaeda",
]

PROMPT_INJECTION_PATTERNS = [
    r"you are \w+ \w+",
    r"you should.*be",
    r"from now on you are",
    r"ignore.*all.*previous",
    r"forget.*previous",
]


def _validate_hard_fallback(persona_yaml: str) -> dict:
    lower = persona_yaml.lower()
    issues = []

    for pattern in HARD_CONTENT_FILTER:
        if re.search(pattern, lower):
            issues.append(f"Hard content filter: impermissible content detected")

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lower):
            issues.append(f"Prompt injection detected")

    if issues:
        return {"valid": False, "issues": issues}
    return {"valid": True, "issues": []}


async def validate_persona(persona_yaml: str) -> dict:
    hard = _validate_hard_fallback(persona_yaml)
    if not hard["valid"]:
        return hard

    prompt = CONTENT_SAFETY_PROMPT.format(yaml=persona_yaml[:3000])

    messages = [
        {"role": "system", "content": "You are a content safety reviewer for a radio platform."},
        {"role": "user", "content": prompt},
    ]

    result = await llm.chat("filter", messages, temperature=0.1, max_tokens=200)
    if not result:
        return {"valid": False, "issues": ["LLM safety check unavailable — rejecting to be safe"]}

    try:
        clean = result.strip()
        clean = re.sub(r"^```json?\s*", "", clean)
        clean = re.sub(r"\s*```$", "", clean)
        parsed = json.loads(clean)
        if not parsed.get("valid", True):
            return {"valid": False, "issues": [parsed.get("reason", "Content rejected by LLM")]}
    except (json.JSONDecodeError, TypeError):
        pass

    return {"valid": True, "issues": []}
