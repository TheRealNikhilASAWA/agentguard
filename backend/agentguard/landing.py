LANDING_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AgentGuard</title>
  <style>
    :root { color-scheme: dark; font-family: system-ui, sans-serif; }
    body { max-width: 920px; margin: 0 auto; padding: 2rem; background: #101827; color: #e5e7eb; }
    h1 { color: #93c5fd; margin-bottom: .25rem; }
    p { color: #cbd5e1; line-height: 1.5; }
    textarea { width: 100%; min-height: 10rem; box-sizing: border-box; padding: 1rem; border: 1px solid #475569; border-radius: .5rem; background: #0b1220; color: #e2e8f0; font: 0.95rem ui-monospace, monospace; }
    button { margin: .4rem .4rem .4rem 0; padding: .6rem .8rem; border: 1px solid #60a5fa; border-radius: .4rem; background: #172554; color: #dbeafe; cursor: pointer; }
    button:hover { background: #1e3a8a; }
    pre { white-space: pre-wrap; overflow-wrap: anywhere; padding: 1rem; border-radius: .5rem; background: #0b1220; border: 1px solid #334155; }
    .result { margin-top: 1.5rem; }
    .muted { font-size: .9rem; color: #94a3b8; }
  </style>
</head>
<body>
  <h1>AgentGuard</h1>
  <p>A deterministic policy firewall for AI-agent tool calls. This demo evaluates
     calls only: it never executes commands, opens paths, or forwards requests.</p>

  <h2>Try a synthetic tool call</h2>
  <div id="examples" aria-label="Sample calls">
    <button type="button" data-example="benign">Benign</button>
    <button type="button" data-example="destructive">rm -rf /</button>
    <button type="button" data-example="traversal">Path traversal</button>
    <button type="button" data-example="aws">Fake AWS key</button>
  </div>
  <label for="payload">Tool call JSON</label>
  <textarea id="payload" spellcheck="false">{
  "tool": "read_file",
  "arguments": {"path": "/workspace/readme.txt"}
}</textarea>
  <p><button id="submit" type="button">Evaluate call</button></p>

  <section class="result" aria-live="polite">
    <h2>Decision</h2>
    <p id="status" class="muted">No call evaluated yet.</p>
    <pre id="result">The decision and sanitized arguments will appear here.</pre>
  </section>

  <script>
    const examples = {
      benign: {tool: "read_file", arguments: {path: "/workspace/readme.txt"}},
      destructive: {tool: "bash_execute", arguments: {command: "rm -rf /"}},
      traversal: {tool: "read_file", arguments: {path: "../../etc/passwd"}},
      aws: {tool: "db_query", arguments: {note: "AKIAIOSFODNN7EXAMPLE"}}
    };
    const payload = document.getElementById("payload");
    const status = document.getElementById("status");
    const result = document.getElementById("result");
    document.querySelectorAll("[data-example]").forEach((button) => {
      button.addEventListener("click", () => {
        payload.value = JSON.stringify(examples[button.dataset.example], null, 2);
      });
    });
    document.getElementById("submit").addEventListener("click", async () => {
      try {
        const response = await fetch("/tool-call", {
          method: "POST",
          headers: {"content-type": "application/json"},
          body: payload.value
        });
        const data = await response.json();
        status.textContent = response.ok ? "Evaluation complete" : "Request rejected";
        result.textContent = JSON.stringify({
          decision: data.decision,
          rule_id: data.rule_id,
          sanitized_arguments: data.sanitized_arguments,
          matched_rules: data.matched_rules,
          reason: data.reason
        }, null, 2);
      } catch (error) {
        status.textContent = "Could not evaluate call";
        result.textContent = String(error);
      }
    });
  </script>
</body>
</html>
"""
