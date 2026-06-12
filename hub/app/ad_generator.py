from __future__ import annotations

import json
import logging
import random
import re

from . import llm

logger = logging.getLogger(__name__)

AD_PROMPT = """Generate a fictional radio spot. Invent an advertising partner, a product, and a key message that would fit a {genre} station.

RULES:
- Advertising partner: a made-up brand name (not a real one)
- Product: a fictional product that matches the genre and target audience
- Key Message: a short, punchy advertising slogan
- Creative, funny, surprising — no standard ad speak
- Station target audience: {audience}

Respond with JSON only:
{{"contributor": "...", "product": "...", "key_message": "..."}}"""


async def generate_random_ad(genre: str = "radio", audience: str = "alle") -> dict:
    prompt = AD_PROMPT.format(genre=genre, audience=audience)

    messages = [
        {"role": "system", "content": "You are a creative copywriter for radio spots."},
        {"role": "user", "content": prompt},
    ]

    result = await llm.chat("filter", messages, temperature=1.0, max_tokens=200)
    if not result:
        return {"contributor": "RADIO FM", "product": "Super Sound", "key_message": "The best sound for your ears"}

    clean = result.strip()
    clean = re.sub(r"^```json?\s*", "", clean)
    clean = re.sub(r"\s*```$", "", clean)

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return {"contributor": "RADIO FM", "product": "Super Sound", "key_message": "The best sound for your ears"}
