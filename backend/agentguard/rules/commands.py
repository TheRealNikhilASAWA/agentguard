from __future__ import annotations

import re


DESTRUCTIVE = [
    re.compile(r"(?:^|[;&|])\s*rm\s+(?:(?:-[rf]+)\s+){1,3}[/~]", re.I),
    re.compile(r"\bmkfs(?:\.[\w-]+)?\b", re.I),
    re.compile(r"\bdd\b[^\n;|]*\bof\s*=\s*/dev/", re.I),
    re.compile(r"\bchmod\s+-R\s+777\b", re.I),
    re.compile(r":\(\)\s*\{.*:\|:.*\}\s*;", re.I),
    re.compile(r"\b(?:shutdown|reboot)\b", re.I),
    re.compile(r">\s*/dev/sda\b", re.I),
]


def destructive_command(value: str) -> str | None:
    for pattern in DESTRUCTIVE:
        if pattern.search(value):
            return "destructive command"
    return None
