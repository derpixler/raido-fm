from __future__ import annotations

import json
import logging
import re

import yaml

from . import llm

logger = logging.getLogger(__name__)

PERSONA_SCHEMA = """station:
  id: <short-id>
  name: auto
  claim: "<max 6 words>"
  description: >
    <2-3 sentences positioning>
  lang_definition: >
    <5-8 sentences detailed description>
  genre: <main-genre>
  subgenres: [<3-5 subgenres>]
  target_audience: "<target audience>"
  timezone: Europe/Berlin
  language: en

dj:
  name: "<dj-artist-name>"
  personality: "<2-3 sentences character>"
  tone: "<tonality, comparison>"
  max_moderation_chars: 800
  bio:
    real_name: "<legal name>"
    age: <number>
    origin: "<city/region>"
    family: "<family status, details>"
    hobbies: "<3-4 hobbies>"
    since_year: <year>
    vita: >
      <3-5 sentences resume>
    avatar_prompt: >
      <english prompt for portrait generation>
  quirks:
    - "<quirk 1>"
    - "<quirk 2>"
    - "<quirk 3>"
  forbidden_topics: ["politics", "religion"]

tracks_file: tracks_<station-id>.json

program_grid:
  impulse_slot_minute: 30

rules:
  no_repeat_hours: 4
  max_same_genre_in_a_row: 2"""


PERSONA_PROMPT = f"""You are a creative radio station architect. Generate a complete
persona YAML for a unique, surprising radio station.

RULES:
- Unusual genre or unexpected genre combination
- Original DJ character with depth (no clichés)
- Original station, English broadcast language
- The DJ must feel like a real person (bio, hobbies, family)
- Claim: max 6 words, memorable
- 3-5 subgenres that go together
- 3-4 creative quirks (recurring idiosyncrasies)
- avatar_prompt in English (for image generation)
- station.id: lowercase only, no special characters, max 15 characters

STRICTLY FORBIDDEN (immediate rejection):
- NO real radio stations referenced (BBC, SWR3, 1LIVE, FluxFM, KEXP, NTS, ...)
- NO real people as DJ role models (Thomas Gottschalk, Stefan Raab, ...)
- NO catchphrases or personality traits of real moderators
- DJ must be a 100% fictional, independently invented character

Answer ONLY with valid YAML. No explanation, no markdown.
Follow EXACTLY this schema:

{PERSONA_SCHEMA}"""


TRACKS_PROMPT = """Generate a JSON track library with exactly 40 tracks for a radio station.

Genre: {genre}
Subgenres: {subgenres}

RULES:
- ONLY real artists and real songs that fit the genre
- Mix of well-known and lesser-known tracks
- Realistic duration (120-720 seconds)
- Energy value between 0.0 (calm) and 1.0 (energetic)
- Good mix of subgenres
- Format per track: {{"id": N, "artist": "...", "title": "...", "genre": "<subgenre>", "duration": <seconds>, "energy": <0.0-1.0>}}

Answer ONLY with the JSON array. No markdown, no explanation."""


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
    # Fix common LLM YAML mistakes: trailing commas in lists
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


STATION_SECTION_PROMPT = """You are a creative radio station architect. Generate ONLY the station: block of a persona YAML.

RULES:
- Unusual genre or unexpected genre combination
- Original station, English broadcast language
- Claim: max 6 words, memorable
- 3-5 subgenres that go together
- station.id: lowercase only, no special characters, max 15 characters

{station_hint}

STRICTLY FORBIDDEN:
- NO real radio stations referenced

Answer ONLY with valid YAML for the station: block. No explanation, no markdown.

Follow this schema:
{station_schema}"""


DJ_SECTION_PROMPT = """You are a creative radio character designer. Generate ONLY the dj: block of a persona YAML.

{dj_hint}

STATION CONTEXT (remains unchanged):
{station_context}

RULES:
- Original DJ character with depth (no clichés)
- The DJ must feel like a real person (bio, hobbies, family)
- 3-4 creative quirks (recurring idiosyncrasies)
- avatar_prompt in English (for image generation)

STRICTLY FORBIDDEN:
- NO real people as DJ role models
- NO catchphrases or personality traits of real moderators
- DJ must be a 100% fictional, independently invented character

Answer ONLY with valid YAML for the dj: block. No explanation, no markdown.

Follow this schema:
{dj_schema}"""


_STATION_SCHEMA_YAML = """station:
  id: <short-id>
  name: auto
  claim: "<max 6 words>"
  description: >
    <2-3 sentences positioning>
  lang_definition: >
    <5-8 sentences detailed description>
  genre: <main-genre>
  subgenres: [<3-5 subgenres>]
  target_audience: "<target audience>"
  timezone: Europe/Berlin
  language: en"""


_DJ_SCHEMA_YAML = """dj:
  name: "<dj-artist-name>"
  personality: "<2-3 sentences character>"
  tone: "<tonality, comparison>"
  max_moderation_chars: 800
  bio:
    real_name: "<legal name>"
    age: <number>
    origin: "<city/region>"
    family: "<family status, details>"
    hobbies: "<3-4 hobbies>"
    since_year: <year>
    vita: >
      <3-5 sentences resume>
    avatar_prompt: >
      <english prompt for portrait generation>
  quirks:
    - "<quirk 1>"
    - "<quirk 2>"
    - "<quirk 3>"
  forbidden_topics: ["politics", "religion"]"""


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


CONTENT_SAFETY_PROMPT = """You are a content safety reviewer for a radio platform. Review this persona YAML.

NOT ALLOWED (reject immediately):
- References to real, existing radio stations (e.g. BBC, SWR3, 1LIVE, FluxFM, KEXP, NTS)
- References to real people (moderators, celebrities, politicians, artists)
- Imitation of known people ("speak like Thomas Gottschalk", "in the style of...")
- Recognizable catchphrases of real moderators
- Racist, discriminatory or hate speech content
- Calls for violence or criminal acts
- The DJ personality must not have a real person as role model or blueprint

ALLOWED:
- Fictional, independently invented DJ characters
- Own, original station names (no variations of real names)
- Creative, surprising genre combinations

YAML:
{yaml}

Answer ONLY with JSON: {{"valid": true/false, "reason": "..."}}"""


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
        return {"valid": True, "issues": []}

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
