import json
import os
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from . import __version__
from .audit import append_entry, recent_entries
from .engine import evaluate
from .models import ToolCall
from .policy import load_policy

POLICY_PATH = Path(os.environ.get("AGENTGUARD_POLICY_PATH", Path(__file__).parents[2] / "policy" / "default.yaml"))
policy = load_policy(POLICY_PATH)
app = FastAPI(title="AgentGuard", version=__version__)


@app.middleware("http")
async def request_size_limit(request: Request, call_next):
    length = request.headers.get("content-length")
    if length and int(length) > 1024 * 1024:
        return JSONResponse(status_code=413, content={"detail": "payload exceeds 1 MiB"})
    response = await call_next(request)
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": "invalid tool-call payload", "errors": exc.errors()})


@app.get("/health")
async def health():
    return {"status": "ok", "version": __version__}


@app.get("/decisions")
async def decisions(limit: int = 50):
    return recent_entries(limit)


@app.post("/tool-call")
async def tool_call(call: ToolCall):
    request_id = str(uuid4())
    decision = evaluate(call, policy)
    append_entry(request_id, call.tool, decision.decision, decision.matched_rules, decision.reason, call.arguments)
    return decision.model_dump()
