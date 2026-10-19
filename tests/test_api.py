import json
from pathlib import Path
from fastapi.testclient import TestClient
from agentguard.api import app


def test_health():
    response = TestClient(app).get("/health")
    assert response.status_code == 200 and response.json() == {"status": "ok", "version": "0.1.0"}


def test_landing_page_has_demo_controls():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    page = response.text
    assert "AgentGuard" in page
    for label in ("Benign", "rm -rf /", "Path traversal", "Fake AWS key"):
        assert label in page
    assert 'fetch("/tool-call"' in page


def test_landing_page_renders_results_as_text():
    page = TestClient(app).get("/").text
    assert "result.textContent" in page
    assert "result.innerHTML" not in page
    assert "<script src=" not in page


def test_api_decision_and_audit(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTGUARD_AUDIT_PATH", str(tmp_path / "audit.jsonl"))
    client = TestClient(app)
    response = client.post("/tool-call", json={"tool": "bash_execute", "arguments": {"command": "rm -rf /"}})
    assert response.status_code == 200 and response.json()["decision"] == "BLOCK"
    entries = client.get("/decisions").json()
    assert entries[0]["decision"] == "BLOCK" and "arguments_sha256" in entries[0]


def test_invalid_payload_is_422():
    response = TestClient(app).post("/tool-call", json={"tool": "read_file"})
    assert response.status_code == 422 and "invalid" in response.json()["detail"]


def test_oversize_payload_is_413():
    response = TestClient(app).post("/tool-call", content=json.dumps({"tool": "read_file", "arguments": {"x": "a" * (1024 * 1024)}}), headers={"content-type": "application/json"})
    assert response.status_code == 413
