"""
DAY 4 — The mission: protected MCP data + shell computation + trace.

READ FIRST:  ../03-putting-it-together.md
(requires src/secure_mcp.py running in another terminal, and 00 + 02 done)

The ONLY async code in this file is GIVEN below, fully commented —
you do not write any async today. (New to async? The 60-second
explainer at the top of src/check_auth.py covers everything used here.)

Your TODOs are all synchronous and small:
  1. import build pieces from your shell_agent (llm, SYSTEM_PROMPT,
     make_backend)
  2. under __main__: backend, cleanup = make_backend()
  3. agent = create_deep_agent(model=..., system_prompt=...,
                               tools=[fetch_internal_report],   # <- the given one
                               backend=backend)
  4. invoke MISSION, print the last message, cleanup in finally.
"""

import asyncio
import json
import os

from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.auth import BearerAuth

load_dotenv()

MCP_URL = os.getenv("MCP_URL", "http://localhost:8002/mcp")
ADMIN_TOKEN = os.getenv("MCP_ADMIN_TOKEN", "admin-secret-token")


# ─────────────────────────────────────────────────────────────────
# GIVEN — do not modify, do read.
#
# This is a completely ORDINARY tool from the agent's point of view:
# a sync function with a docstring that returns a string. The agent
# never knows that inside it, a network protocol and a bearer token
# do the actual work. Hiding machinery behind a boring interface is
# the same trick as Day 3's build_agent() — one level down.
# ─────────────────────────────────────────────────────────────────
def fetch_internal_report() -> str:
    """Fetch the protected quarterly report from the secure MCP server."""

    async def _call() -> str:
        # `async with` opens the MCP connection and guarantees it is
        # closed afterwards — even if the call in the middle raises.
        # BearerAuth attaches "Authorization: Bearer <token>" to every
        # request; without it the server answers 401 before any tool
        # is even visible (you proved this with check_auth.py).
        async with Client(MCP_URL, auth=BearerAuth(token=ADMIN_TOKEN)) as c:
            result = await c.call_tool("get_internal_report", {})
            # result.data is already parsed structured content;
            # we serialize it so the tool returns a plain string,
            # which every model handles happily.
            return json.dumps(result.data)

    # asyncio.run = the single bridge from the sync world (this tool)
    # into the async world (the MCP client) and back. It starts an
    # event loop, runs _call() to completion, returns its value.
    return asyncio.run(_call())


MISSION = (
    "1. Call fetch_internal_report to get the quarterly data. "
    "2. Write analyze.py that computes total revenue, total costs, and "
    "profit margin per month from that data. "
    "3. Execute it with python. "
    "4. Report exactly what the program printed, plus one sentence of insight."
)


if __name__ == "__main__":
    # TODO (all sync, ~8 lines):
    #   backend, cleanup = make_backend()
    #   try:
    #       agent = create_deep_agent(... tools=[fetch_internal_report] ...)
    #       result = agent.invoke({"messages": [{"role": "user", "content": MISSION}]})
    #       print(result["messages"][-1].content)
    #   finally:
    #       cleanup()
    pass
