from __future__ import annotations

import json
import logging
import random
import re

from . import llm
from .prompt_loader import load_prompt

logger = logging.getLogger(__name__)

AD_PROMPT = load_prompt("ads/ad.prompt")


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
