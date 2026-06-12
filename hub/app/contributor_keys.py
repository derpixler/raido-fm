from __future__ import annotations

import logging
from collections import deque
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

CONTRIBUTORS_PATH = Path("/app/contributors.yml")
_contributors: list[dict] = []
_contributor_queue: deque = deque()
_current_contributor: dict | None = None


def load_contributors() -> list[dict]:
    global _contributors, _contributor_queue
    try:
        if not CONTRIBUTORS_PATH.exists():
            return []
        with open(CONTRIBUTORS_PATH) as f:
            data = yaml.safe_load(f)
        _contributors = sorted(
            data.get("contributors", []),
            key=lambda s: s.get("priority", 99),
        )
        _contributor_queue = deque(
            [s for s in _contributors if s.get("priority", 0) > 0 and s.get("api_key")]
        )
        logger.info("Loaded %d contributors (%d active)", len(_contributors), len(_contributor_queue))
    except Exception as e:
        logger.warning("Failed to load contributors: %s", e)
        _contributors = []
    return _contributors


def get_fallback_config() -> dict | None:
    for s in _contributors:
        if s.get("priority", 0) == 0:
            return s
    return None


def get_current_contributor_config() -> dict | None:
    global _current_contributor
    if not _contributors:
        load_contributors()

    if _current_contributor:
        budget = _current_contributor.get("token_budget", 0)
        used = _current_contributor.get("token_used", 0)
        if budget == 0 or used < budget:
            return _current_contributor

    if _contributor_queue:
        _current_contributor = _contributor_queue.popleft()
        logger.info("Switched to contributor: %s", _current_contributor["name"])
        return _current_contributor

    fallback = get_fallback_config()
    if fallback:
        logger.info("Using fallback contributor: %s", fallback["name"])
        return fallback

    return None


def record_token_usage(tokens: int) -> None:
    if _current_contributor:
        _current_contributor["token_used"] = _current_contributor.get("token_used", 0) + tokens


def get_all_contributors() -> list[dict]:
    if not _contributors:
        load_contributors()
    return _contributors


def save_contributor(name: str, data: dict) -> None:
    all_contributors = get_all_contributors()
    for i, s in enumerate(all_contributors):
        if s["name"] == name:
            all_contributors[i] = data
            break
    else:
        all_contributors.append(data)

    with open(CONTRIBUTORS_PATH, "w") as f:
        yaml.dump({"contributors": sorted(all_contributors, key=lambda s: s.get("priority", 99))}, f, allow_unicode=True)
    load_contributors()
