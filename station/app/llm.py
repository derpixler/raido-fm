from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from typing import Any

import httpx
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

_ROLE_CONFIGS: dict[str, dict[str, str]] = {}
_clients: dict[str, AsyncOpenAI] = {}
_usage: dict[str, dict[str, int | float]] = {}
_active_contributor_name: str | None = None
_station_id: str = os.getenv("STATION_ID", "unknown")

HUB_URL = os.getenv("HUB_URL", "")
HUB_ADMIN_TOKEN = os.getenv("HUB_ADMIN_TOKEN", "")


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


def get_active_contributor_name() -> str | None:
    return _active_contributor_name


def reset_usage() -> None:
    _usage.clear()


async def _report_to_hub(
    contributor_name: str,
    role: str,
    operation: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    latency_ms: float,
) -> None:
    if not HUB_URL or not HUB_ADMIN_TOKEN:
        return
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.post(
                f"{HUB_URL}/contributors/report-usage",
                json={
                    "contributor_name": contributor_name,
                    "station_id": _station_id,
                    "role": role,
                    "operation": operation,
                    "model": model,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "latency_ms": latency_ms,
                },
                headers={"Authorization": f"Bearer {HUB_ADMIN_TOKEN}"},
            )
    except Exception:
        pass


async def chat(
    role: str,
    messages: list[dict[str, str]],
    temperature: float = 0.8,
    max_tokens: int = 1024,
    operation: str = "",
) -> str | None:
    global _active_contributor_name

    cfg = _get_role_config(role)
    client = _get_client(role)
    _active_contributor_name = None
    try:
        from pathlib import Path
        import yaml
        ct_file = Path("/app/contributors.yml")
        if ct_file.exists():
            ct_data = yaml.safe_load(ct_file.read_text())
            ct_list = ct_data.get("contributors", []) if ct_data else []
            active = [s for s in ct_list if s.get("api_key") and s.get("priority", 0) > 0]
            if active:
                ct = active[0]
                _active_contributor_name = ct.get("name", "")
                cfg = {"model": ct.get("api_model", cfg["model"]), "base_url": ct.get("api_base_url", cfg["base_url"]), "api_key": ct["api_key"]}
                client = AsyncOpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
    except Exception:
        pass

    if not _active_contributor_name:
        _active_contributor_name = _env("LLM_DJ_API_KEY", "")[:16] + "..." if _env("LLM_DJ_API_KEY") else "owner-fallback"

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

        if HUB_URL and response and hasattr(response, "usage") and response.usage:
            asyncio.create_task(_report_to_hub(
                contributor_name=_active_contributor_name,
                role=role,
                operation=operation or _default_operation(role),
                model=cfg["model"],
                prompt_tokens=response.usage.prompt_tokens or 0,
                completion_tokens=response.usage.completion_tokens or 0,
                total_tokens=response.usage.total_tokens or 0,
                latency_ms=latency,
            ))

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

            if HUB_URL and response and hasattr(response, "usage") and response.usage:
                asyncio.create_task(_report_to_hub(
                    contributor_name=_active_contributor_name,
                    role="fallback",
                    operation=operation or _default_operation(role),
                    model=fallback_model,
                    prompt_tokens=response.usage.prompt_tokens or 0,
                    completion_tokens=response.usage.completion_tokens or 0,
                    total_tokens=response.usage.total_tokens or 0,
                    latency_ms=latency,
                ))

            return response.choices[0].message.content
        except Exception as e:
            _record_error("fallback")
            logger.error("Fallback LLM also failed: %s", e)

    return None


def _default_operation(role: str) -> str:
    if role == "dj":
        return "moderation"
    elif role == "filter":
        return "sanitize"
    return role


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
