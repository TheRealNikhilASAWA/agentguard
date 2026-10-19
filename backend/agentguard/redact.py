import copy
import re
from typing import Any

EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PHONE = re.compile(r"(?<!\w)(?:(?:\+?\d[ ()-]*){10,12})(?!\w)")
AWS = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
GITHUB = re.compile(r"\b(?:ghp|gho)_[A-Za-z0-9]{20,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b")
JWT = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
PEM = re.compile(r"-----BEGIN [^-]+-----.*?-----END [^-]+-----", re.S)
BEARER = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]{8,}")
OPENAI = re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")
GENERIC = re.compile(r"(?i)\b(password|secret|token|api[_ -]?key)\b\s*[:=]\s*([^,;\s]{8,})")
CARD = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")


def luhn(value: str) -> bool:
    digits = re.sub(r"[ -]", "", value)
    total = 0
    for index, digit in enumerate(reversed(digits)):
        number = int(digit) * (2 if index % 2 else 1)
        total += number - 9 if number > 9 else number
    return len(digits) in range(13, 20) and total % 10 == 0


def redact_string(value: str) -> tuple[str, bool]:
    changed = False

    def replace(pattern: re.Pattern[str], label: str, text: str) -> str:
        nonlocal changed
        result, count = pattern.subn(lambda m: f"[REDACTED:{label}]", text)
        changed = changed or count > 0
        return result

    value = replace(PEM, "private_key", value)
    value = replace(AWS, "aws_key", value)
    value = replace(GITHUB, "github_token", value)
    value = replace(OPENAI, "api_key", value)
    value = replace(JWT, "jwt", value)
    value = replace(BEARER, "bearer", value)
    value = replace(GENERIC, "secret", value)
    def card(match: re.Match[str]) -> str:
        nonlocal changed
        if luhn(match.group(0)):
            changed = True
            return "[REDACTED:credit_card]"
        return match.group(0)

    value = CARD.sub(card, value)
    value = replace(EMAIL, "email", value)
    value = replace(PHONE, "phone", value)
    return value, changed


def redact(value: Any) -> tuple[Any, bool]:
    if isinstance(value, dict):
        result = {}
        changed = False
        for key, item in value.items():
            redacted, item_changed = redact(item)
            result[key] = redacted
            changed = changed or item_changed
        return result, changed
    if isinstance(value, list):
        result = [redact(item) for item in value]
        return [item[0] for item in result], any(item[1] for item in result)
    if isinstance(value, str):
        return redact_string(value)
    return copy.deepcopy(value), False
