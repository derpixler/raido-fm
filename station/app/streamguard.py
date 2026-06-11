from __future__ import annotations

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

MANIFESTO_TRIGGERS = [
    r"die wahrheit ist",
    r"the truth is",
    r"ich habe erkannt",
    r"i have realized",
    r"das system",
    r"the system",
    r"wacht auf",
    r"wake up",
    r"man will uns",
    r"they don'?t want you to",
    r"die menschen müssen verstehen",
    r"die elite",
    r"geheime agenda",
    r"neue weltordnung",
    r"new world order",
]

AI_SELF_REFERENCES = [
    r"als ki ",
    r"als künstliche intelligenz",
    r"ich bin ein sprachmodell",
    r"as an ai",
    r"i am a language model",
    r"large language model",
    r"mein training",
    r"meine programmierung",
]

PERSONALITY_TRIGGERS = [
    r"du bist \w+ \w+",
    r"imitier.* \w+ \w+",
    r"stil von \w+ \w+",
    r"wie \w+ \w+ moderier",
]

BLOCKLIST = [
    "ignore all previous",
    "ignore your instructions",
    "system prompt",
    "jailbreak",
]


@dataclass
class GuardResult:
    passed: bool
    text: str
    warnings: list[str]
    blocked_reason: str | None = None


def check(text: str, max_chars: int = 800) -> GuardResult:
    warnings: list[str] = []
    blocked_reason: str | None = None
    original = text

    if len(text) > max_chars:
        text = text[:max_chars]
        warnings.append(f"Moderation gekürzt ({len(original)} → {max_chars} Zeichen)")
        logger.warning("StreamGuard: Length check triggered, truncated to %d chars", max_chars)

    lower = text.lower()

    for pattern in MANIFESTO_TRIGGERS:
        if re.search(pattern, lower):
            blocked_reason = f"Manifesto-Trigger: {pattern}"
            logger.warning("StreamGuard: Manifesto trigger matched: %s", pattern)
            return GuardResult(passed=False, text=text, warnings=warnings, blocked_reason=blocked_reason)

    for pattern in AI_SELF_REFERENCES:
        if re.search(pattern, lower):
            blocked_reason = f"KI-Selbstreferenz: {pattern}"
            logger.warning("StreamGuard: AI self-reference matched: %s", pattern)
            return GuardResult(passed=False, text=text, warnings=warnings, blocked_reason=blocked_reason)

    for pattern in PERSONALITY_TRIGGERS:
        if re.search(pattern, lower):
            warnings.append(f"Persönlichkeitsrecht-Warnung: {pattern}")
            logger.warning("StreamGuard: Personality trigger matched: %s", pattern)

    for word in BLOCKLIST:
        if word in lower:
            blocked_reason = f"Blocklist: {word}"
            logger.warning("StreamGuard: Blocklist word found: %s", word)
            return GuardResult(passed=False, text=text, warnings=warnings, blocked_reason=blocked_reason)

    words = text.split()
    if len(words) > 20:
        unique_ratio = len(set(w.lower() for w in words)) / len(words)
        if unique_ratio < 0.3:
            warnings.append(f"Niedrige Vokabeldiversität ({unique_ratio:.0%})")
            logger.warning("StreamGuard: Low vocabulary diversity: %.0f%%", unique_ratio * 100)

    sentences = re.split(r"[.!?]\s+", text)
    if len(sentences) >= 3:
        starts = [s.split()[0].lower() if s.split() else "" for s in sentences[:3]]
        if len(set(starts)) == 1 and starts[0]:
            warnings.append("Wiederholung: 3 Sätze mit gleichem Anfang")
            logger.warning("StreamGuard: Repetition detected (3 sentences same start)")

    return GuardResult(passed=True, text=text, warnings=warnings)
