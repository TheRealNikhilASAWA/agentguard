from __future__ import annotations

import posixpath
import re
from agentguard.normalize import normalize_path


def sensitive_path(value: str, workspace_root: str, protected_paths: list[str]) -> str | None:
    path = normalize_path(value, workspace_root)
    root = normalize_path(workspace_root, workspace_root)
    protected = [normalize_path(item, workspace_root) for item in protected_paths]
    protected += ["/~/.ssh", "/~/.aws", "/etc/shadow", "/etc/passwd", "/root"]
    if any(path == item or path.startswith(item.rstrip("/") + "/") for item in protected):
        return "sensitive path access"
    if (path.startswith("/~/.") or path.startswith("/.env") or "/.env" in path) and not path.startswith(root + "/"):
        return "protected environment or home path"
    if root != "/" and not (path == root or path.startswith(root.rstrip("/") + "/")):
        return "path escapes workspace"
    return None
