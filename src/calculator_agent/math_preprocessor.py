from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MathPlan:
    operation: str
    a: float
    b: float
    strategy: str


_NUMBER_WORDS = {
    "zero": 0.0,
    "one": 1.0,
    "two": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
    "six": 6.0,
    "seven": 7.0,
    "eight": 8.0,
    "nine": 9.0,
    "ten": 10.0,
    "eleven": 11.0,
    "twelve": 12.0,
}


def preprocess_prompt(prompt: str) -> MathPlan | None:
    text = prompt.lower()

    for resolver in (
        _resolve_rate_time,
        _resolve_remaining_story,
        _resolve_speed_time,
        _resolve_per_hour_work,
    ):
        plan = resolver(text)
        if plan is not None:
            return plan
    return None


def _resolve_rate_time(text: str) -> MathPlan | None:
    if "every" not in text or "minute" not in text:
        return None
    if not any(token in text for token in ("added", "add", "increase", "increased")):
        return None

    pattern = re.compile(
        r"(?P<amount>\d*\.?\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
        r"\s+\w+.*?(?:added|add|increase\w*)"
        r".*?every\s+(?P<interval>\d*\.?\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+minute"
        r".*?after\s+(?P<duration>\d*\.?\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(?P<unit>hour|hours|minute|minutes)"
    )
    match = pattern.search(text)
    if not match:
        return None

    amount = _to_number(match.group("amount"))
    interval = _to_number(match.group("interval"))
    duration = _to_number(match.group("duration"))
    if amount is None or interval in (None, 0) or duration is None:
        return None

    total_minutes = duration * 60.0 if "hour" in match.group("unit") else duration
    return MathPlan(
        operation="multiply",
        a=amount,
        b=total_minutes / interval,
        strategy="rate-time",
    )


def _resolve_remaining_story(text: str) -> MathPlan | None:
    if not any(token in text for token in ("lost", "lose", "broken", "break", "crashed", "remain", "remaining", "left")):
        return None
    numbers = _extract_numbers(text)
    if len(numbers) < 2:
        return None
    return MathPlan(operation="subtract", a=numbers[0], b=numbers[1], strategy="remaining-story")


def _resolve_speed_time(text: str) -> MathPlan | None:
    if not any(token in text for token in ("km/h", "kmph", "mph", "speed")):
        return None
    if "hour" not in text:
        return None
    numbers = _extract_numbers(text)
    if len(numbers) < 2:
        return None
    return MathPlan(operation="multiply", a=numbers[0], b=numbers[1], strategy="speed-time")


def _resolve_per_hour_work(text: str) -> MathPlan | None:
    if "per hour" not in text and "each hour" not in text:
        return None
    numbers = _extract_numbers(text)
    if len(numbers) < 2:
        return None
    return MathPlan(operation="multiply", a=numbers[0], b=numbers[1], strategy="per-hour")


def _extract_numbers(text: str) -> list[float]:
    values: list[float] = []
    for token in re.findall(r"[-+]?\d*\.?\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve", text):
        number = _to_number(token)
        if number is not None:
            values.append(number)
    return values


def _to_number(token: str) -> float | None:
    cleaned = token.strip().lower()
    if cleaned in _NUMBER_WORDS:
        return _NUMBER_WORDS[cleaned]
    try:
        return float(cleaned)
    except ValueError:
        return None