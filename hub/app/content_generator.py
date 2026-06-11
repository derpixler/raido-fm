from __future__ import annotations

import json
import logging
import re

from . import llm

logger = logging.getLogger(__name__)

POPULATE_PROMPT = """Generiere einen kurzen, realistischen Radio-{category}-Eintrag fuer eine {genre}-Station.

REGELN:
- Max 200 Zeichen
- Passend zum Genre "{genre}" und zur Stimmung der Station
- Realistisch, nicht uebertrieben
- Bei "listener_comment": ein fiktiver Hoerer-Kommentar mit Vornamen
- Bei "music_request": ein plausibler Musikwunsch passend zum Genre
- Bei "news": eine erfundene, genre-nahe Nachricht
- Bei "weather": ein kurzer Wetterbericht

Antworte nur mit dem Text. Kein JSON, kein Markdown."""


async def generate_content(category: str, genre: str = "radio") -> str:
    cat_names = {
        "listener_comment": "Hoerer-Kommentar",
        "music_request": "Musikwunsch",
        "news": "Nachricht",
        "weather": "Wetterbericht",
    }
    cat_name = cat_names.get(category, category)
    prompt = POPULATE_PROMPT.format(category=cat_name, genre=genre)

    messages = [
        {"role": "system", "content": "Du bist ein kreativer Texter fuer Radio-Inhalte."},
        {"role": "user", "content": prompt},
    ]

    result = await llm.chat("filter", messages, temperature=1.0, max_tokens=300)
    if result:
        return result.strip()[:200]
    return f"[{cat_name}] Keine Daten verfuegbar."
