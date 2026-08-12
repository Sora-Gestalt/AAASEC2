"""
DAY 3 — HTTP API (SOLUTION).

Three endpoints, three ideas:

  GET  /healthz                        -> "is the process alive?" (Docker needs this)
  POST /v1/responses                   -> OpenResponses-shaped chat endpoint
  GET  /.well-known/agent-card.json    -> A2A discovery: "who am I, what can I do?"

We implement a deliberately SMALL SUBSET of the OpenResponses shape:
enough that any OpenResponses-aware client (including the Vite frontend
you'll build later) can talk to us, without drowning in the full spec.
The lesson is the boundary itself:  API contract != agent implementation.
"""

import os
import time
import uuid

from fastapi import FastAPI
from pydantic import BaseModel

try:  # running as a package (uvicorn src.api:app)
    from .agent import build_agent
except ImportError:  # running the file directly
    from agent import build_agent

STUDENT_NAME = os.getenv("STUDENT_NAME", "anonymous-student")
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:8000")

app = FastAPI(title=f"AAASEC2 agent — {STUDENT_NAME}")

# Built ONCE at startup, not per request. The API holds a reference to
# "an agent", whatever build_agent decided that means today.
agent = build_agent()


# ---------- request/response models (OpenResponses subset) ----------

class ResponseRequest(BaseModel):
    input: str                     # full spec allows rich item lists; we accept plain text
    model: str | None = None       # accepted for shape-compatibility; we ignore it


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/v1/responses")
async def create_response(request: ResponseRequest):
    started = time.time()

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": request.input}]}
    )
    text = result["messages"][-1].content

    # OpenResponses-shaped reply: a response object whose `output` is a
    # list of items; ours is a single assistant message with output_text.
    return {
        "id": f"resp_{uuid.uuid4().hex[:24]}",
        "object": "response",
        "created_at": int(started),
        "status": "completed",
        "model": request.model or "aaasec2-deep-agent",
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": text}],
            }
        ],
    }


# ---------- A2A discovery ----------

@app.get("/.well-known/agent-card.json")
async def agent_card():
    """The Agent Card: how OTHER agents discover what this one can do.

    A2A standardizes discovery around this well-known path. We serve a
    spec-shaped card whose `url` points at our OpenResponses endpoint;
    the official a2a-sdk with its full task protocol is the bonus in
    09-a2a.md.
    """
    return {
        "protocolVersion": "1.0",
        "name": f"{STUDENT_NAME}-agent",
        "description": (
            "AAASEC2 Day 3 student agent: research briefs, arithmetic, "
            "current time, and filesystem-scoped skills."
        ),
        "url": f"{PUBLIC_URL}/v1/responses",
        "version": "0.1.0",
        "capabilities": {"streaming": False},
        "defaultInputModes": ["text/plain"],
        "defaultOutputModes": ["text/plain"],
        "skills": [
            {
                "id": "research-brief",
                "name": "Research brief",
                "description": "One-page structured executive research brief on a technical topic.",
                "tags": ["research", "writing"],
            },
            {
                "id": "calculate",
                "name": "Calculator",
                "description": "Basic arithmetic evaluation.",
                "tags": ["math"],
            },
        ],
    }
