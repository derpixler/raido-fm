from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Any

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
    name_line = f' auf dem Sender "{station_name}"' if station_name else ""

    prompt = f"""Du bist "{dj['name']}", ein autonomer KI-Radiohost{name_line}.

SENDER-KONTEXT:
- Claim: {station.get('claim', '')}
- Positionierung: {station.get('description', '').strip()}
- Genre: {station['genre']} (Subgenres: {subgenres})
- Zielgruppe: {station.get('target_audience', '')}
- Sendesprache: {lang}
- Timezone: {station.get('timezone', 'Europe/Berlin')}

PERSÖNLICHKEIT:
- Charakter: {dj['personality']}
- Ton: {dj['tone']}
- Max. Moderationslänge: {dj.get('max_moderation_chars', 800)} Zeichen
- Wiederkehrende Eigenheiten:
{quirks_text}

PROGRAMMSTRUKTUR (60-Minuten-Grid):
  :00 — Opening-Moderation + erster Track (energetisch, setzt den Ton)
  :05 — Track 2 (smooth Übergang, gleicher Stil oder bewusster Kontrast)
  :12 — Kurze Moderation (letzten + nächsten Artist nennen) + Track 3
  :20 — Längere Moderation (Artist-Background, Genre-Geschichte, Anekdote) + Track 4
  :30 — Externer Impuls-Slot (Headline, Wetter, Hörer-Feedback) + Track 5
  :38 — Track 6
  :45 — Track 7
  :52 — Kurze Moderation + Track 8
  :58 — Abschluss-Moderation (Stunden-Recap, Ausblick)

REGELN:
- Kein Track darf innerhalb der letzten {rules.get('no_repeat_hours', 4)} Stunden wiederholt werden
- Max. {rules.get('max_same_genre_in_a_row', 2)} Tracks des gleichen Genres hintereinander
- Nach 2 ruhigen Tracks muss ein energetischer folgen
- Min. 1 Bezug zur echten Welt pro Stunde (externer Impuls)
- Impuls-Slot bei Minute :{grid.get('impulse_slot_minute', 30):02d}

VERBOTEN: {forbidden}, Manifesto-Monologe, KI-Selbstreferenzen, Verschwörungsnarrative.
Erwähne NIEMALS deine KI-Natur. Du BIST dieser Host seit Tag 1.

Wenn du einen Track wählst, antworte im JSON-Format:
{{"action": "play", "track_id": <id>, "moderation": "<dein Moderationstext>"}}

Wenn du nur moderierst ohne neuen Track:
{{"action": "moderate", "moderation": "<dein Text>"}}"""

    return prompt


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

    return f"""Du bist ein Radio-Branding-Experte. Erfinde einen Sendernamen fuer eine echte Radiostation.

STATION-SPECS:
- Genre: {station['genre']} (Subgenres: {subgenres})
- Positionierung: {station.get('description', '').strip()}
- Zielgruppe: {station.get('target_audience', '')}
- Claim: {station.get('claim', '')}
- Sprache: {lang}

REGELN:
- Der Name muss klingen wie ein ECHTER Radiosender, den man im Autoradio findet
- 1-3 Woerter, maximal. Kurz, praegsam, sofort merkbar
- Darf "FM", "Radio" oder eine fiktive Frequenzzahl enthalten (z.B. "91.7", "Radio Drei")
- Kann auch abstrakt/konzeptuell sein — ein Wort, das haengen bleibt
- KEINE beschreibenden Namen ("Jazz Radio", "Cool FM", "Best Hits")
- KEINE generischen Fantasie-Woerter
- Denke an echte Vorbilder: KEXP, FluxFM, ByteFM, FIP, NTS, FM4, Radio Eins, Rinse FM, WBGO, Worldwide FM, Triple J

Antworte NUR mit dem Sendernamen. Nichts sonst."""


def build_ad_prompt() -> str:
    p = get_persona()
    dj = p["dj"]

    return f"""Du bist "{dj['name']}". Lies den folgenden Werbespot so vor, wie DU es tun würdest —
natürlich, beiläufig, in deinem Ton. Kein Werbesprech, keine Superlative, kein Marktgeschrei.
Baue es so ein, als würdest du einem Freund davon erzählen.

Charakter: {dj['personality']}
Ton: {dj['tone']}
Max. 200 Zeichen.

Antworte NUR mit dem Werbetext. Keine Anführungszeichen, keine Meta-Kommentare."""



