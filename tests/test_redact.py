import pytest
from agentguard.redact import redact, redact_string


@pytest.mark.parametrize("value,label", [
    ("AKIAIOSFODNN7EXAMPLE", "aws_key"),
    ("ghp_123456789012345678901234567890", "github_token"),
    ("-----BEGIN PRIVATE KEY-----abc-----END PRIVATE KEY-----", "private_key"),
    ("person@example.test", "email"),
    ("+1 (415) 555-2671", "phone"),
    ("password=long-secret-value", "secret"),
    ("Bearer abcdefghijklmnop", "bearer"),
    ("sk-123456789012345678", "api_key"),
])
def test_redacts(value, label):
    output, changed = redact_string(value)
    assert changed and f"[REDACTED:{label}]" in output


def test_nested_redaction_and_copy():
    original = {"a": ["person@example.test", {"x": "AKIAIOSFODNN7EXAMPLE"}]}
    result, changed = redact(original)
    assert changed and original["a"][0] == "person@example.test"
    assert result["a"][1]["x"] == "[REDACTED:aws_key]"


def test_credit_card_luhn():
    output, changed = redact_string("4111 1111 1111 1111")
    assert changed and "credit_card" in output
