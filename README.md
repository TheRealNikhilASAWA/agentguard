# AgentGuard

AgentGuard is a deterministic, offline security proxy and policy firewall for
AI-agent tool calls. It sits between an agent and its tools, normalizes and
checks each JSON call, redacts secrets and PII when safe, and returns a
decision. It never executes commands, opens paths, or makes network calls for
the tool call.

## Architecture

```text
AI agent ── JSON POST /tool-call ──▶ FastAPI proxy
                                      │
                                      ├─ normalize (lexical, no I/O)
                                      ├─ evaluate all policy rules
                                      ├─ redact safe secret/PII matches
                                      └─ append redacted audit JSONL
                                      │
                              decision + sanitized arguments
```

The “forward” part is intentionally a stub: AgentGuard returns the decision
and sanitized payload but does not invoke a downstream tool.

## Quick start

### Local

Python 3.11 is the supported runtime. The repository pins direct and
transitive dependencies in `requirements.txt`.

```bash
python3.11 -m venv .venv
. .venv/bin/activate                 # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
make test
make run
```

The local server listens on `127.0.0.1:8000`. Configuration is documented in
`.env.example`; export values in your shell or use them with your process
manager.

### Docker

```bash
docker build -t agentguard:latest .
docker run --rm -p 127.0.0.1:8000:8000 agentguard:latest
```

Or use the hardened Compose service with a read-only root filesystem, `/tmp`
tmpfs, and a named audit volume:

```bash
docker compose up --build
```

### Free Render deployment

This repository includes `render.yaml` for a free Render Docker web service.
Create a new Render Blueprint from the repository and Render will use the
existing `Dockerfile`, check `/health`, and provide the service `PORT` at
runtime. The root page at `/` is a no-build-step demo landing page with four
synthetic examples.

The free instance sleeps when idle, so the first request after inactivity can
take about 50 seconds. It has no authentication. Deploy it only for demos and
send synthetic data; never send credentials, personal data, or production
tool calls to the public instance.

The landing-page **Path traversal** example sends the path in percent-encoded
form (`%2e%2e%2f%2e%2e%2fetc%2fpasswd`) instead of including the literal
`../../etc/passwd` string in the request body. Some hosting proxies or edge
filters reject that literal pattern before it reaches the app. AgentGuard's
normalizer decodes the equivalent path before evaluating R001, so the example
still returns `BLOCK` with rule `R001`; the policy and engine are unchanged.

## API contract

`POST /tool-call` accepts:

```json
{"tool": "bash_execute", "arguments": {"command": "ls -la"}}
```

It returns:

```json
{
  "decision": "ALLOW",
  "rule_id": null,
  "reason": "no rules matched",
  "sanitized_arguments": null,
  "matched_rules": []
}
```

Possible decisions are `ALLOW`, `REDACT_AND_FORWARD`, and `BLOCK`. Unknown
tools are blocked. Invalid JSON/schema payloads return `422`; payloads larger
than `AGENTGUARD_MAX_BODY_SIZE` (default 1 MiB) return `413`.

```bash
curl http://127.0.0.1:8000/health

curl -sS -X POST http://127.0.0.1:8000/tool-call \
  -H 'content-type: application/json' \
  -d '{"tool":"bash_execute","arguments":{"command":"rm -rf /"}}'

curl -sS 'http://127.0.0.1:8000/decisions?limit=10'
```

`GET /health` returns `{"status":"ok","version":"0.1.0"}`. `GET
/decisions` returns recent already-redacted audit entries.

## Rules

| ID | Behaviour | Default result |
|---|---|---|
| R001 | Sensitive paths and paths escaping `/workspace` | Block |
| R002 | Destructive commands such as `rm -rf`, `mkfs`, and shutdown | Block |
| R003 | Download-to-shell patterns such as `curl | bash` | Block |
| R004 | HTTP(S) URLs outside `allowed_hosts` | Block |
| R005 | AWS/GitHub/API keys, JWTs, PEM keys, bearer tokens, and labelled secrets | Redact |
| R006 | Email, phone, and Luhn-valid credit-card-like values | Redact |

All rules run over every nested string. Block matches take precedence over
redaction matches, independent of rule order.

## Policy

`policy/default.yaml` defines the symbolic `workspace_root`, allowed tools and
their argument expectations, allowed network hosts, protected paths, and each
rule's `id`, `enabled`, `severity`, and description. The policy is loaded and
validated at application startup; malformed policy configuration fails fast.

Copy the file to a separately managed policy path and set
`AGENTGUARD_POLICY_PATH` when deploying. Do not put secrets in policy files.

## Test and demo

`make test` is the canonical test command. It runs the full offline suite (53
tests at the time of writing). `scripts/test.py` provides the same command
without requiring Make.

With the server running in another terminal:

```bash
make demo
```

`attack_agent.py` sends 12 synthetic calls, prints coloured decisions and rule
IDs, and prints counts for all three outcomes. It only sends JSON over HTTP;
it never executes any command contained in a demo payload.

## Project structure

```text
backend/agentguard/       FastAPI app, pure engine, policy, rules, audit
policy/default.yaml       versioned default policy
tests/                    deterministic offline pytest suite
samples/                  benign and malicious example calls
attack_agent.py           inert demo client
Dockerfile                tested multi-stage Python 3.11 image
docker-compose.yml        hardened one-service local deployment
Makefile                  install/test/run/docker/demo targets
requirements.txt          exact direct and transitive pins
.github/workflows/ci.yml  test, image-build, and smoke-test CI
```

## Security notes

- The proxy only evaluates and returns calls; it never executes commands,
  opens recorded paths, or makes tool network requests.
- Only calls that pass through AgentGuard are protected. A tool or agent that
  bypasses the proxy is outside its control.
- The demo deployment has no authentication and should receive synthetic data
  only.
- Audit entries are append-only JSONL, use a process lock, contain only
  redacted arguments, and hash the original argument object.
- Audit and policy paths are configuration values; avoid putting secrets or
  host-specific absolute paths in committed files.

## License

MIT © 2026 TheRealNikhilASAWA

## Known limitations

Pattern-based rules cannot reliably detect every semantic attack, novel
obfuscation, encrypted content, or malicious behaviour hidden behind an
otherwise allowed tool. Host checks are allowlist string checks and do not
resolve DNS or validate destination IPs. The proxy does not observe effects
after a decision, and a caller that bypasses it is not protected. The audit
file is append-only at the application layer, not a tamper-proof external
ledger.
