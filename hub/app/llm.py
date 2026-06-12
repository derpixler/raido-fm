from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

_ROLE_CONFIGS: dict[str, dict[str, str]] = {}
_clients: dict[str, AsyncOpenAI] = {}
_usage: dict[str, dict[str, int | float]] = {}


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _get_role_config(role: str) -> dict[str, str]:
    if role not in _ROLE_CONFIGS:
        prefix = f"LLM_{role.upper()}_"
        base_url = _env(f"{prefix}BASE_URL", _env("LLM_DJ_BASE_URL", "https://api.groq.com/openai/v1"))
        model = _env(f"{prefix}MODEL", _env("LLM_DJ_MODEL", "llama-3.3-70b-versatile"))
        api_key = _env(f"{prefix}API_KEY", _env("LLM_DJ_API_KEY", ""))
        _ROLE_CONFIGS[role] = {"base_url": base_url, "model": model, "api_key": api_key}
    return _ROLE_CONFIGS[role]


def _get_client(role: str) -> AsyncOpenAI:
    if role not in _clients:
        cfg = _get_role_config(role)
        _clients[role] = AsyncOpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
    return _clients[role]


def _get_fallback_client() -> AsyncOpenAI | None:
    base_url = _env("LLM_FALLBACK_BASE_URL")
    api_key = _env("LLM_FALLBACK_API_KEY")
    if not base_url or not api_key:
        return None
    if "fallback" not in _clients:
        _clients["fallback"] = AsyncOpenAI(base_url=base_url, api_key=api_key)
    return _clients["fallback"]


def _record_usage(role: str, response, latency_ms: float) -> None:
    if role not in _usage:
        _usage[role] = {
            "calls": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "total_latency_ms": 0.0,
            "last_latency_ms": 0.0,
            "errors": 0,
        }
    bucket = _usage[role]
    bucket["calls"] += 1
    bucket["total_latency_ms"] += latency_ms
    bucket["last_latency_ms"] = latency_ms
    if response and hasattr(response, "usage") and response.usage:
        bucket["prompt_tokens"] += response.usage.prompt_tokens or 0
        bucket["completion_tokens"] += response.usage.completion_tokens or 0
        bucket["total_tokens"] += response.usage.total_tokens or 0


def _record_error(role: str) -> None:
    if role not in _usage:
        _usage[role] = {
            "calls": 0, "prompt_tokens": 0, "completion_tokens": 0,
            "total_tokens": 0, "total_latency_ms": 0.0, "last_latency_ms": 0.0,
            "errors": 0,
        }
    _usage[role]["errors"] += 1


def get_usage() -> dict[str, dict[str, int | float]]:
    result = {}
    for role, bucket in _usage.items():
        calls = bucket["calls"]
        result[role] = {
            **bucket,
            "avg_latency_ms": round(bucket["total_latency_ms"] / calls, 1) if calls else 0,
            "model": _get_role_config(role).get("model", "unknown") if role != "fallback" else _env("LLM_FALLBACK_MODEL", "deepseek-chat"),
        }
    return result


def reset_usage() -> None:
    _usage.clear()


async def chat(
    role: str,
    messages: list[dict[str, str]],
    temperature: float = 0.8,
    max_tokens: int = 1024,
) -> str | None:
    # Sponsor key override
    try:
        from . import sponsor_keys
        sponsor = sponsor_keys.get_current_sponsor_config()
        if sponsor and sponsor.get("api_key"):
            cfg = {
                "model": sponsor.get("api_model", "deepseek-chat"),
                "base_url": sponsor.get("api_base_url", "https://api.deepseek.com"),
                "api_key": sponsor["api_key"],
            }
            client = AsyncOpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
        else:
            cfg = _get_role_config(role)
            client = _get_client(role)
    except ImportError:
        cfg = _get_role_config(role)
        client = _get_client(role)

    try:
        t0 = time.monotonic()
        response = await client.chat.completions.create(
            model=cfg["model"],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency = (time.monotonic() - t0) * 1000
        _record_usage(role, response, latency)
        # Track sponsor tokens
        if response and hasattr(response, "usage") and response.usage:
            try:
                from . import sponsor_keys
                sponsor_keys.record_token_usage(response.usage.total_tokens or 0)
            except ImportError:
                pass
        return response.choices[0].message.content
    except Exception as e:
        _record_error(role)
        logger.warning("LLM call failed for role=%s: %s", role, e)

    fallback = _get_fallback_client()
    if fallback:
        fallback_model = _env("LLM_FALLBACK_MODEL", "deepseek-chat")
        try:
            t0 = time.monotonic()
            response = await fallback.chat.completions.create(
                model=fallback_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            latency = (time.monotonic() - t0) * 1000
            _record_usage("fallback", response, latency)
            return response.choices[0].message.content
        except Exception as e:
            _record_error("fallback")
            logger.error("Fallback LLM also failed: %s", e)

    return None


def parse_json_response(text: str) -> dict[str, Any] | None:
    text = text.strip()

    md_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if md_match:
        text = md_match.group(1)

    json_match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Could not parse JSON from LLM response: %.200s", text)
        return None


def reset_clients() -> None:
    _ROLE_CONFIGS.clear()
    _clients.clear()
