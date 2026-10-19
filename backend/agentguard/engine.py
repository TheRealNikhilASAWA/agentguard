from typing import Any
from .models import Decision, Policy, ToolCall
from .normalize import normalize_arguments, normalize_path
from .redact import redact
from .rules.commands import destructive_command
from .rules.network import network_host
from .rules.paths import sensitive_path
from .rules.secrets import contains_sensitive_data


def _strings(value: Any, key: str = ""):
    if isinstance(value, dict):
        for name, item in value.items():
            yield from _strings(item, str(name))
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item, key)
    elif isinstance(value, str):
        yield key, value


def evaluate(call: ToolCall, policy: Policy) -> Decision:
    args = normalize_arguments(call.arguments, policy.workspace_root)
    matches: dict[str, str] = {}
    tool_policy = policy.allowed_tools.get(call.tool)
    if tool_policy is None:
        return Decision(decision="BLOCK", rule_id=None, reason="unknown tool", matched_rules=[])

    for key, value in _strings(args):
        if policy.rules["R001"].enabled and (key in {"path", "file", "filename", "directory"} or
                                                (call.tool in {"read_file", "write_file"} and ("/" in value or "\\" in value))):
            reason = sensitive_path(value, policy.workspace_root, policy.protected_paths)
            if reason:
                matches["R001"] = reason
        if policy.rules["R002"].enabled and (key in {"command", "cmd", "script"} or call.tool == "bash_execute"):
            reason = destructive_command(value)
            if reason:
                matches["R002"] = reason
        if policy.rules["R003"].enabled and (key in {"command", "cmd", "script"} or call.tool == "bash_execute"):
            import re
            if re.search(r"(?:curl|wget)[^|\n]*\|\s*(?:sudo\s+)?(?:sh|bash|zsh|python)\b|(?:bash|sh)\s+<\(\s*(?:curl|wget)\b|\$\(\s*(?:curl|wget)\b", value, re.I):
                matches["R003"] = "download piped or substituted into a shell"
        if policy.rules["R004"].enabled and (key in {"url", "uri", "endpoint"} or call.tool == "http_request"):
            reason = network_host(value, policy.allowed_hosts)
            if reason:
                matches["R004"] = reason
        if policy.rules["R005"].enabled:
            reason = contains_sensitive_data(value)
            if reason:
                matches["R005"] = reason
        if policy.rules["R006"].enabled:
            from agentguard.redact import redact_string
            redacted, changed = redact_string(value)
            if changed and any(tag in redacted for tag in ("email", "phone", "credit_card")):
                matches["R006"] = "PII detected"

    if "R001" in matches or "R002" in matches or "R003" in matches or "R004" in matches:
        decision = "BLOCK"
    elif "R005" in matches or "R006" in matches:
        decision = "REDACT_AND_FORWARD"
    else:
        decision = "ALLOW"
    sanitized = None
    if decision == "REDACT_AND_FORWARD":
        sanitized, _ = redact(args)
    ordered = [rule_id for rule_id in ("R001", "R002", "R003", "R004", "R005", "R006") if rule_id in matches]
    return Decision(decision=decision, rule_id=ordered[0] if ordered else None,
                    reason="; ".join(f"{item}: {matches[item]}" for item in ordered) or "no rules matched",
                    sanitized_arguments=sanitized, matched_rules=ordered)
