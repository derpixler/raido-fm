from __future__ import annotations

import json
import logging
import re

from . import llm

logger = logging.getLogger(__name__)

POPULATE_PROMPT = """Generate a short, realistic radio {category} entry for a {genre} station.

RULES:
- Max 200 characters
- Matching the genre "{genre}" and the station's mood
- Realistic, not exaggerated
- For "listener_comment": a fictional listener comment with a first name
- For "music_request": a plausible music request matching the genre
- For "news": a made-up, genre-appropriate news item
- For "weather": a short weather report

Respond with text only. No JSON, no Markdown."""


async def generate_content(category: str, genre: str = "radio") -> str:
    cat_names = {
        "listener_comment": "Listener Comment",
        "music_request": "Music Request",
        "news": "News",
        "weather": "Weather Report",
    }
    cat_name = cat_names.get(category, category)
    prompt = POPULATE_PROMPT.format(category=cat_name, genre=genre)

    messages = [
        {"role": "system", "content": "You are a creative copywriter for radio content."},
        {"role": "user", "content": prompt},
    ]

    result = await llm.chat("filter", messages, temperature=1.0, max_tokens=300)
    if result:
        return result.strip()[:200]
    return f"[{cat_name}] No data available."
