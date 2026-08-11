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
import time
import uuid
import typing
from fastapi import FastAPI
from pydantic import BaseModel
from src.agent import build_agent
app = FastAPI(title="Deep Agent service",version="1.0.0")
agent = build_agent()


class ResponseRequest(BaseModel):
   input:str
   model: typing.Optional[str]="default"
   
class TextContent(BaseModel):
   type:str = "output_text"
   text:str
   
class OutputMessage(BaseModel):
   type:str = "message"
   role:str = "assistant"
   content: list[TextContent]
   
class OpenResponsesResponse(BaseModel):
    id: str
    object: str = "response"
    created_at: int
    status: str = "completed"
    model: str
    output: list[OutputMessage]
    
   



@app.get("/healthz")
async def healthz():
    """Health check endpoint used by Docker and orchestrators."""
    return {"status": "ok"}
 
 
@app.post("/v1/responses", response_model=OpenResponsesResponse)
async def create_response(body: ResponseRequest):
    """Exposes the agent through the OpenResponses API shape."""
    # Invoke agent with input adhering to .ainvoke({"messages": [...]})
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": body.input}]}
    )

    # Extract response content handling dict or LangChain BaseMessage objects
    messages = response.get("messages", [])
    if messages:
        last_msg = messages[-1]
        text_content = (
            last_msg.content
            if hasattr(last_msg, "content")
            else last_msg.get("content", "")
        )
    else:
        text_content = str(response)

    # Wrap reply in standard OpenResponses response object
    return OpenResponsesResponse(
        id=f"resp_{uuid.uuid4().hex[:12]}",
        object="response",
        created_at=int(time.time()),
        status="completed",
        model=body.model or "default",
        output=[
            OutputMessage(
                type="message",
                role="assistant",
                content=[TextContent(type="output_text", text=str(text_content))],
            )
        ],
    )