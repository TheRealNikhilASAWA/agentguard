import json
from agentguard.audit import append_entry


def test_audit_is_redacted_and_append_only(tmp_path, monkeypatch):
    path = tmp_path / "audit.jsonl"
    monkeypatch.setenv("AGENTGUARD_AUDIT_PATH", str(path))
    append_entry("1", "db_query", "REDACT_AND_FORWARD", ["R005"], "secret", {"value": "AKIAIOSFODNN7EXAMPLE"})
    append_entry("2", "db_query", "ALLOW", [], "ok", {"value": "safe"})
    text = path.read_text()
    assert "AKIAIOSFODNN7EXAMPLE" not in text
    assert len(text.splitlines()) == 2
    assert json.loads(text.splitlines()[0])["redacted_arguments"]["value"] == "[REDACTED:aws_key]"
