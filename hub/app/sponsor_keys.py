from __future__ import annotations

import logging
from collections import deque
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

SPONSORS_PATH = Path("/app/sponsors.yml")
_sponsors: list[dict] = []
_sponsor_queue: deque = deque()
_current_sponsor: dict | None = None


def load_sponsors() -> list[dict]:
    global _sponsors, _sponsor_queue
    try:
        if not SPONSORS_PATH.exists():
            return []
        with open(SPONSORS_PATH) as f:
            data = yaml.safe_load(f)
        _sponsors = sorted(
            data.get("sponsors", []),
            key=lambda s: s.get("priority", 99),
        )
        # Queue: all non-fallback sponsors sorted by priority
        _sponsor_queue = deque(
            [s for s in _sponsors if s.get("priority", 0) > 0 and s.get("api_key")]
        )
        logger.info("Loaded %d sponsors (%d active)", len(_sponsors), len(_sponsor_queue))
    except Exception as e:
        logger.warning("Failed to load sponsors: %s", e)
        _sponsors = []
    return _sponsors


def get_fallback_config() -> dict | None:
    for s in _sponsors:
        if s.get("priority", 0) == 0:
            return s
    return None


def get_current_sponsor_config() -> dict | None:
    global _current_sponsor
    if not _sponsors:
        load_sponsors()

    if _current_sponsor:
        budget = _current_sponsor.get("token_budget", 0)
        used = _current_sponsor.get("token_used", 0)
        if budget == 0 or used < budget:
            return _current_sponsor

    if _sponsor_queue:
        _current_sponsor = _sponsor_queue.popleft()
        logger.info("Switched to sponsor: %s", _current_sponsor["name"])
        return _current_sponsor

    fallback = get_fallback_config()
    if fallback:
        logger.info("Using fallback sponsor: %s", fallback["name"])
        return fallback

    return None


def record_token_usage(tokens: int) -> None:
    if _current_sponsor:
        _current_sponsor["token_used"] = _current_sponsor.get("token_used", 0) + tokens


def get_all_sponsors() -> list[dict]:
    if not _sponsors:
        load_sponsors()
    return _sponsors


def save_sponsor(name: str, data: dict) -> None:
    all_sponsors = get_all_sponsors()
    for i, s in enumerate(all_sponsors):
        if s["name"] == name:
            all_sponsors[i] = data
            break
    else:
        all_sponsors.append(data)

    with open(SPONSORS_PATH, "w") as f:
        yaml.dump({"sponsors": sorted(all_sponsors, key=lambda s: s.get("priority", 99))}, f, allow_unicode=True)
    load_sponsors()
