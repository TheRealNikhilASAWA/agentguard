from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: str = Field(min_length=1, max_length=200)
    arguments: dict[str, Any]


class Decision(BaseModel):
    decision: Literal["ALLOW", "REDACT_AND_FORWARD", "BLOCK"]
    rule_id: Optional[str] = None
    reason: str
    sanitized_arguments: Optional[Dict[str, Any]] = None
    matched_rules: List[str] = Field(default_factory=list)


class PolicyRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    enabled: bool = True
    severity: Literal["low", "medium", "high", "critical"]
    description: str


class ToolPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    arguments: dict[str, str] = Field(default_factory=dict)


class Policy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    workspace_root: str
    allowed_tools: dict[str, ToolPolicy]
    allowed_hosts: list[str] = Field(default_factory=list)
    protected_paths: list[str] = Field(default_factory=list)
    rules: dict[str, PolicyRule]
