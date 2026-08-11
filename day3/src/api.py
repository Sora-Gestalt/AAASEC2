"""
DAY 3 — HTTP API.

READ FIRST:  ../03-fastapi-openresponses.md
             ../09-a2a.md   (for the agent card endpoint)

Do not continue to 04-docker.md until:
    curl http://localhost:8000/healthz            -> {"status":"ok"}
    curl -X POST http://localhost:8000/v1/responses \
         -H 'Content-Type: application/json' -d '{"input":"hi"}'
returns an OpenResponses-shaped JSON object.

TODO:
  1. app = FastAPI(...); agent = build_agent()   <- built ONCE, at startup
  2. GET  /healthz
  3. POST /v1/responses  — accept {"input": "...", "model": optional},
     invoke the agent, return:
       {id, object:"response", created_at, status:"completed", model,
        output:[{type:"message", role:"assistant",
                 content:[{type:"output_text", text: ...}]}]}
     (a deliberate SUBSET of OpenResponses — the shape, not the whole spec)
  4. GET /.well-known/agent-card.json — your A2A Agent Card. Use
     STUDENT_NAME and PUBLIC_URL from the environment; the card's "url"
     field must point at YOUR /v1/responses.
"""

# TODO
