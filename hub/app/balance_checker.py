from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


@dataclass
class BalanceInfo:
    provider: str
    balance: str | None = None
    currency: str | None = None
    is_estimate: bool = False
    error: str | None = None


async def check_balance(api_key: str, base_url: str) -> BalanceInfo:
    host = urlparse(base_url).hostname or ""

    if "deepseek" in host:
        return await _check_deepseek(api_key)
    elif "openrouter" in host:
        return await _check_openrouter(api_key)
    elif "openai" in host:
        return _check_estimate("openai")
    elif "groq" in host:
        return _check_estimate("groq")
    else:
        return _check_estimate("unknown")


async def _check_deepseek(api_key: str) -> BalanceInfo:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.deepseek.com/user/balance",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("is_available") and data.get("balance_infos"):
                    info = data["balance_infos"][0]
                    return BalanceInfo(
                        provider="deepseek",
                        balance=info.get("total_balance", "0"),
                        currency=info.get("currency", "CNY"),
                        is_estimate=False,
                    )
            return BalanceInfo(
                provider="deepseek",
                error=f"API returned {resp.status_code}",
                is_estimate=True,
            )
    except Exception as e:
        logger.warning("DeepSeek balance check failed: %s", e)
        return BalanceInfo(provider="deepseek", error=str(e), is_estimate=True)


async def _check_openrouter(api_key: str) -> BalanceInfo:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://openrouter.ai/api/v1/credits",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                total = data.get("total_credits", 0)
                used = data.get("total_usage", 0)
                remaining = total - used
                return BalanceInfo(
                    provider="openrouter",
                    balance=str(remaining),
                    currency="USD",
                    is_estimate=False,
                )
            return BalanceInfo(
                provider="openrouter",
                error=f"API returned {resp.status_code}",
                is_estimate=True,
            )
    except Exception as e:
        logger.warning("OpenRouter balance check failed: %s", e)
        return BalanceInfo(provider="openrouter", error=str(e), is_estimate=True)


def _check_estimate(provider: str) -> BalanceInfo:
    return BalanceInfo(
        provider=provider,
        balance=None,
        is_estimate=True,
        error=f"{provider} does not expose a public balance endpoint",
    )
