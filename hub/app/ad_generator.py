from __future__ import annotations

import json
import logging
import random
import re

from . import llm

logger = logging.getLogger(__name__)

AD_PROMPT = """Generiere einen fiktiven Radiospot. Erfinde einen Werbepartner, ein Produkt und eine Kernbotschaft, die zu einer {genre}-Station passen wuerde.

REGELN:
- Werbepartner: ein erfundener Markenname (kein echter)
- Produkt: ein fiktives Produkt das zum Genre und zur Zielgruppe passt
- Key Message: ein kurzer, praegnanter Werbespruch
- Kreativ, witzig, ueberraschend — kein Standard-Werbesprech
- Zielgruppe der Station: {audience}

Antworte nur mit JSON:
{{"contributor": "...", "product": "...", "key_message": "..."}}"""


async def generate_random_ad(genre: str = "radio", audience: str = "alle") -> dict:
    prompt = AD_PROMPT.format(genre=genre, audience=audience)

    messages = [
        {"role": "system", "content": "Du bist ein kreativer Werbetexter fuer Radio-Spots."},
        {"role": "user", "content": prompt},
    ]

    result = await llm.chat("filter", messages, temperature=1.0, max_tokens=200)
    if not result:
        return {"contributor": "RADIO FM", "product": "Super Sound", "key_message": "Der beste Sound fuer deine Ohren"}

    clean = result.strip()
    clean = re.sub(r"^```json?\s*", "", clean)
    clean = re.sub(r"\s*```$", "", clean)

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return {"contributor": "RADIO FM", "product": "Super Sound", "key_message": "Der beste Sound fuer deine Ohren"}
