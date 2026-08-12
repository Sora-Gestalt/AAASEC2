"""
DAY 4 — The mission (SOLUTION): all three pieces in one task.

                      LangSmith
                         ▲ traces (env vars — zero code)
                         │
    User ──► Deep Agent ─┤
              │          │
              │ tool     │ backend
              ▼          ▼
    Authenticated MCP   Sandbox
    (information)       (computation)

Task: fetch data from the PROTECTED tool, write an analysis program
IN the sandbox, execute it, report the result. Every piece must work
or the mission fails — that's the design.

Run the secure MCP server first (src/secure_mcp.py), then:
    uv run python src/mission.py
Then open the trace in LangSmith and follow what actually happened.
"""

import asyncio
import json
import os

from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.auth import BearerAuth

# reuse yesterday's lesson: build on the pieces you already have
from shell_agent import SYSTEM_PROMPT, llm, make_backend
from deepagents import create_deep_agent

load_dotenv()

MCP_URL = os.getenv("MCP_URL", "http://localhost:8002/mcp")
TOKEN = os.getenv("MCP_ADMIN_TOKEN", "admin-secret-token")


def fetch_internal_report() -> str:
    """Fetch the protected quarterly report from the secure MCP server.

    (A plain tool that speaks MCP inside — the agent doesn't know or
    care that a network protocol and a bearer token live in here.)
    """
    async def _call():
        async with Client(MCP_URL, auth=BearerAuth(token=TOKEN)) as c:
            result = await c.call_tool("get_internal_report", {})
            return json.dumps(result.data)

    return asyncio.run(_call())


MISSION = (
    "1. Call fetch_internal_report to get the quarterly data. "
    "2. Write analyze.py in your sandbox that computes total revenue, "
    "total costs, and profit margin per month from that data. "
    "3. Execute it. 4. Report the numbers and one sentence of insight."
)


if __name__ == "__main__":
    backend, cleanup = make_backend()
    try:
        agent = create_deep_agent(
            model=llm,
            system_prompt=SYSTEM_PROMPT,
            tools=[fetch_internal_report],
            backend=backend,
        )
        result = agent.invoke({"messages": [{"role": "user", "content": MISSION}]})
        print(result["messages"][-1].content)
    finally:
        cleanup()
