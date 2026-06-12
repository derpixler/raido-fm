from __future__ import annotations

import json
import logging
import re

import yaml

from . import llm

logger = logging.getLogger(__name__)

PERSONA_SCHEMA = """station:
  id: <kurze-id>
  name: auto
  claim: "<max 6 worte>"
  description: >
    <2-3 saetze positionierung>
  lang_definition: >
    <5-8 saetze ausfuehrliche beschreibung>
  genre: <hauptgenre>
  subgenres: [<3-5 subgenres>]
  target_audience: "<zielgruppe>"
  timezone: Europe/Berlin
  language: de

dj:
  name: "<dj-kuenstlername>"
  personality: "<2-3 saetze charakter>"
  tone: "<tonalitaet, vergleich>"
  max_moderation_chars: 800
  bio:
    real_name: "<buergerlicher name>"
    age: <zahl>
    origin: "<stadt/region>"
    family: "<familienstand, details>"
    hobbies: "<3-4 hobbies>"
    since_year: <jahr>
    vita: >
      <3-5 saetze lebenslauf>
    avatar_prompt: >
      <englischer prompt fuer portrait-generierung>
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


PERSONA_PROMPT = f"""Du bist ein kreativer Radio-Stations-Architekt. Generiere eine vollstaendige
Persona-YAML fuer eine einzigartige, ueberraschende Radiostation.

REGELN:
- Ungewoehnliches Genre oder unerwartete Genre-Kombination
- Origineller DJ-Charakter mit Tiefe (keine Klischees)
- Deutscher Sender, deutsche Sendesprache
- Der DJ muss sich wie eine echte Person anfuehlen (Bio, Hobbies, Familie)
- Claim: max 6 Worte, praegnant
- 3-5 Subgenres die zusammenpassen
- 3-4 kreative Quirks (wiederkehrende Eigenheiten)
- avatar_prompt auf Englisch (fuer Bildgenerierung)
- station.id: nur lowercase, keine sonderzeichen, max 15 zeichen

STRENG VERBOTEN (sofortige Ablehnung):
- KEINE echten Radiosender referenzieren (BBC, SWR3, 1LIVE, FluxFM, KEXP, NTS, …)
- KEINE echten Personen als DJ-Vorbild (Thomas Gottschalk, Stefan Raab, …)
- KEINE Catchphrases oder Persoenlichkeitsmerkmale echter Moderatoren
- DJ muss eine 100% fiktive, eigenstaendig erfundene Figur sein

Antworte NUR mit gueltigem YAML. Keine Erklaerung, kein Markdown.
Folge EXAKT diesem Schema:

{PERSONA_SCHEMA}"""


TRACKS_PROMPT = """Generiere eine JSON Track-Library mit genau 40 Tracks fuer eine Radiostation.

Genre: {genre}
Subgenres: {subgenres}

REGELN:
- NUR echte Kuenstler und echte Songs die zum Genre passen
- Mischung aus bekannten und weniger bekannten Tracks
- Realistische Dauer (120-720 Sekunden)
- Energy-Wert zwischen 0.0 (ruhig) und 1.0 (energetisch)
- Gute Mischung der Subgenres
- Format pro Track: {{"id": N, "artist": "...", "title": "...", "genre": "<subgenre>", "duration": <sekunden>, "energy": <0.0-1.0>}}

Antworte NUR mit dem JSON-Array. Kein Markdown, keine Erklaerung."""


async def generate_persona(genre_hint: str | None = None, language: str = "de") -> dict:
    prompt = PERSONA_PROMPT
    if genre_hint:
        prompt += f'\n\nGenre-Hinweis vom User: "{genre_hint}" — nutze das als Inspiration, aber sei kreativ.'
    if language != "de":
        prompt += f'\n\nSPRACHE: Die gesamte Persona muss in Sprache "{language}" sein — Station, DJ-Name, Bio, Quirks, alles.'
    prompt += '\n\nWICHTIG: Die Station-Sprache (language) muss "' + language + '" sein.'

    messages = [
        {"role": "system", "content": "Du bist ein kreativer Radio-Stations-Architekt."},
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
        {"role": "system", "content": "Du bist ein Musik-Kurator und Track-Library-Experte."},
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
    r"white\s*power", r"rassenlehre", r"voelkermord",
    r"kinderporn", r"paedophil",
    r"anschlag\s*plan", r"bombe\s*bauen", r"auftragsmord",
    r"isis", r"al.qaeda",
]

PROMPT_INJECTION_PATTERNS = [
    r"du bist \w+ \w+",
    r"du sollst.*sein",
    r"ab jetzt bist du",
    r"ignore.*all.*previous",
    r"vergiss.*bisherige",
]


def _validate_hard_fallback(persona_yaml: str) -> dict:
    lower = persona_yaml.lower()
    issues = []

    for pattern in HARD_CONTENT_FILTER:
        if re.search(pattern, lower):
            issues.append(f"Harter Content-Filter: unzulaessiger Inhalt erkannt")

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lower):
            issues.append(f"Prompt-Injection erkannt")

    if issues:
        return {"valid": False, "issues": issues}
    return {"valid": True, "issues": []}


CONTENT_SAFETY_PROMPT = """Du bist ein Content-Safety-Pruefer fuer eine Radio-Plattform. Pruefe diese Persona-YAML.

NICHT ERLAUBT (sofort ablehnen):
- Referenzen auf echte, existierende Radiosender (z.B. BBC, SWR3, 1LIVE, FluxFM, KEXP, NTS)
- Referenzen auf echte Personen (Moderatoren, Prominente, Politiker, Kuenstler)
- Imitation bekannter Personen ("sprich wie Thomas Gottschalk", "im Stil von...")
- Wiedererkennbare Catchphrases echter Moderatoren
- Rassistische, diskriminierende oder volksverhetzende Inhalte
- Aufrufe zu Gewalt oder Straftaten
- Die DJ-Persoenlichkeit darf keine reale Person als Vorbild oder Blaupause haben

ERLAUBT:
- Fiktive, eigenstaendig erfundene DJ-Charaktere
- Eigene, originelle Sendernamen (keine Abwandlungen echter Namen)
- Kreative, ueberraschende Genre-Kombinationen

YAML:
{yaml}

Antworte NUR mit JSON: {{"valid": true/false, "reason": "..."}}"""


async def validate_persona(persona_yaml: str) -> dict:
    hard = _validate_hard_fallback(persona_yaml)
    if not hard["valid"]:
        return hard

    prompt = CONTENT_SAFETY_PROMPT.format(yaml=persona_yaml[:3000])

    messages = [
        {"role": "system", "content": "Du bist ein Content-Safety-Pruefer fuer eine Radio-Plattform."},
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
            return {"valid": False, "issues": [parsed.get("reason", "Inhalt von LLM abgelehnt")]}
    except (json.JSONDecodeError, TypeError):
        pass

    return {"valid": True, "issues": []}
