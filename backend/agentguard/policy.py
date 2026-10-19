from __future__ import annotations

from pathlib import Path
import yaml
from pydantic import ValidationError
from .models import Policy


def load_policy(path: str | Path) -> Policy:
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
        if not isinstance(raw, dict):
            raise ValueError("policy must be a YAML mapping")
        policy = Policy.model_validate(raw)
        if set(policy.rules) != {"R001", "R002", "R003", "R004", "R005", "R006"}:
            raise ValueError("policy must define exactly R001 through R006")
        return policy
    except (OSError, yaml.YAMLError, ValidationError, ValueError) as exc:
        raise RuntimeError(f"invalid AgentGuard policy: {exc}") from exc
