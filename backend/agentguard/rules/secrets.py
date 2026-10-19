from __future__ import annotations

from agentguard.redact import redact_string


def contains_sensitive_data(value: str) -> str | None:
    return "secret or PII detected" if redact_string(value)[1] else None
