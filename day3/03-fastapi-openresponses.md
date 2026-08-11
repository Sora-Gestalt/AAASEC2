# 03 — FastAPI + OpenResponses: the agent becomes a service

**Edit:** `src/api.py`

## The conceptual transition of the whole day

```
Day 1:  Python program → LangGraph
Day 2:  Python program → multi-agent system
Day 3:  NETWORK SERVICE → agent
```

Until now, using your agent meant importing your Python. From now on, using your agent means speaking HTTP to a port. Who can use it just changed from "you" to "anything with a network stack" — including, later today, other students' agents, and in a later session, a Vite frontend.

## Why OpenResponses instead of inventing `POST /chat`

You could invent your own request shape today and regret your youthful mistakes when the frontend arrives. Instead, expose the **OpenResponses** shape from day one: a provider-independent contract (modeled on the Responses API) for request/response structure, output items, tool invocations, and streaming semantics. The payoff is the separation:

```
API contract  ≠  agent implementation
```

Behind `/v1/responses` you can put `create_deep_agent`, Day 2's supervisor, a raw LangGraph, or some monstrosity you invent next Thursday. The client cannot tell, and must not care. **We implement a deliberate subset** — plain-text `input`, one assistant message out — not the full specification. The lesson is the boundary, not spec coverage.

## Your task

In `src/api.py`:

1. `app = FastAPI(...)` and `agent = build_agent()` **once at module import** — not per request. (Why? What would per-request construction cost you?)
2. `GET /healthz` → `{"status": "ok"}`. Trivial now; Docker and the shared server will *live* on this endpoint.
3. `POST /v1/responses` — accept `{"input": str, "model": optional}`, `await agent.ainvoke(...)`, wrap the last message as:

```json
{
  "id": "resp_…", "object": "response", "created_at": 1754900000,
  "status": "completed", "model": "…",
  "output": [{"type": "message", "role": "assistant",
              "content": [{"type": "output_text", "text": "…"}]}]
}
```

4. `GET /.well-known/agent-card.json` — stub it now returning `{"todo": true}`; you'll fill it properly in `09-a2a.md`.

## Verify

```bash
USE_FAKE=1 uv run uvicorn src.api:app --port 8000 --reload
```

From a **second terminal** (get used to this — services and clients are different processes):

```bash
curl http://localhost:8000/healthz
curl -X POST http://localhost:8000/v1/responses \
     -H 'Content-Type: application/json' \
     -d '{"input": "write a research brief on tethered drones"}'
```

Also open http://localhost:8000/docs — FastAPI generated interactive API docs from your type hints. That's what a *contract* buys you.

Then kill the server, drop `USE_FAKE`, and run it against the real agent once.

## ✅ Git checkpoint

```bash
git add day3/src/api.py
git commit -m "day3: expose agent through FastAPI (OpenResponses subset)"
```

→ Continue to `04-docker.md`
