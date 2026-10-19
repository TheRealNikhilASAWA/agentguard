from __future__ import annotations

from urllib.parse import urlparse


def network_host(value: str, allowed_hosts: list[str]) -> str | None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    host = parsed.hostname.lower()
    allowed = {item.lower() for item in allowed_hosts}
    if host not in allowed and not any(host.endswith("." + item) for item in allowed):
        return "network host is not allowed"
    return None
