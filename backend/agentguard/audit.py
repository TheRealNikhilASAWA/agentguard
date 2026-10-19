from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from .redact import redact

_lock = Lock()


def audit_path() -> Path:
    return Path(os.environ.get("AGENTGUARD_AUDIT_PATH", "./audit/audit.jsonl"))


def append_entry(request_id: str, tool: str, decision: str, rule_ids: list[str], reason: str,
                 original_arguments: Any) -> None:
    redacted, _ = redact(original_arguments)
    raw = json.dumps(original_arguments, sort_keys=True, separators=(",", ":"), default=str).encode()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "request_id": request_id,
        "tool": tool,
        "decision": decision,
        "rule_ids": rule_ids,
        "reason": reason,
        "arguments_sha256": hashlib.sha256(raw).hexdigest(),
        "redacted_arguments": redacted,
    }
    path = audit_path()
    with _lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")


def recent_entries(limit: int = 50) -> list[dict[str, Any]]:
    path = audit_path()
    if not path.exists():
        return []
    with _lock:
        with path.open("r", encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
    return entries[-max(0, min(limit, 500)):][::-1]
