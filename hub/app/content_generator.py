from __future__ import annotations

import json
import logging
import re

from . import llm
from .md_loader import load_prompt

logger = logging.getLogger(__name__)

POPULATE_PROMPT = load_prompt("content/populate.md")


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
