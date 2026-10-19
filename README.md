# AgentGuard

AgentGuard is a deterministic, offline security proxy foundation for AI agent
tool calls. It evaluates requests and returns a decision; it never executes a
command, opens a path, or makes a network request on behalf of a tool.

## Setup

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

```bash
python -m uvicorn agentguard.api:app --app-dir backend
```

Then POST JSON to `http://127.0.0.1:8000/tool-call`. The default audit file is
`./audit/audit.jsonl`; set `AGENTGUARD_AUDIT_PATH` to choose another relative
or symbolic path.

## Test

```bash
python -m pytest -q
```

All tests are offline and deterministic.

## Deploy

Install the pinned `requirements.txt` in a Python 3.11 environment and run the
Uvicorn command above behind the deployment's process supervisor. No external
service is required by AgentGuard itself.
