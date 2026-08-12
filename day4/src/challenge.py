"""
DAY 4 — CHALLENGE template (heavily scaffolded — read top to bottom).

READ FIRST:  ../04-challenge.md

This file is a fill-in-the-blanks walkthrough. Every ▢ marks a spot
where you write a few lines; everything else is done and commented.
If you completed 00-03, each blank is something you have already
written once today. Total new code: roughly 25 lines.

The shape of what you're building:

    your prompt
        │
        ▼
    Deep Agent ──(tool)──► your authenticated MCP server   [information]
        │
        └──(backend)─────► execute on your machine          [computation]
                                    │
                              LangSmith trace               [visibility]

Run order:
    terminal 1:  uv run python src/secure_mcp.py
    terminal 2:  uv run python src/challenge.py
    browser   :  smith.langchain.com -> project aaasec2-day4 -> your run
"""

import asyncio
import json
import os

from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.auth import BearerAuth

from deepagents import create_deep_agent

# Reuse what you already built. If your names differ, fix the import,
# not your files.
from shell_agent import SYSTEM_PROMPT, llm, make_backend

load_dotenv()

MCP_URL = os.getenv("MCP_URL", "http://localhost:8002/mcp")
ADMIN_TOKEN = os.getenv("MCP_ADMIN_TOKEN", "admin-secret-token")


# ════════════════════════════════════════════════════════════════
# STEP 1 — your own protected capability
# ════════════════════════════════════════════════════════════════
# The mission used OUR get_internal_report. The challenge wants YOUR
# data behind YOUR protected tool.
#
# ▢ 1a. In src/secure_mcp.py, add ONE more protected tool that serves
#       data you invent — sensor readings, grades, lab inventory,
#       anything with a few numbers in it. Copy the exact pattern of
#       get_internal_report (same decorator, same scope) and restart
#       the server.
#
# ▢ 1b. Put its tool name here:

MY_TOOL_NAME = "..."          # <- e.g. "get_lab_inventory"


# ════════════════════════════════════════════════════════════════
# STEP 2 — the tool wrapper (given; identical to mission.py's)
# ════════════════════════════════════════════════════════════════
# Sync outside, async inside, asyncio.run as the bridge. Explained
# line by line in src/mission.py and src/check_auth.py — this is the
# third time you've seen it, which is the point.

def fetch_my_data() -> str:
    """Fetch my protected dataset from my secure MCP server."""

    async def _call() -> str:
        async with Client(MCP_URL, auth=BearerAuth(token=ADMIN_TOKEN)) as c:
            result = await c.call_tool(MY_TOOL_NAME, {})
            return json.dumps(result.data)

    return asyncio.run(_call())


# ════════════════════════════════════════════════════════════════
# STEP 3 — your task prompt
# ════════════════════════════════════════════════════════════════
# ▢ Write a MISSION for your data. Keep the mission.py rhythm:
#     fetch -> write a program -> execute it -> report what it printed.
#   The "report exactly what the program printed" clause is what lets
#   you catch the model summarizing instead of computing.

MISSION = (
    "1. Call fetch_my_data to get the data. "
    "2. Write a Python program that computes ... "        # ▢ your analysis
    "3. Execute it with python. "
    "4. Report exactly what the program printed, plus one insight."
)


# ════════════════════════════════════════════════════════════════
# STEP 4 — assemble and run (given)
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    backend, cleanup = make_backend()
    try:
        agent = create_deep_agent(
            model=llm,
            system_prompt=SYSTEM_PROMPT,
            tools=[fetch_my_data],
            backend=backend,
        )
        result = agent.invoke({"messages": [{"role": "user", "content": MISSION}]})
        print(result["messages"][-1].content)
    finally:
        cleanup()


# ════════════════════════════════════════════════════════════════
# STEP 5 — evidence (nothing to code)
# ════════════════════════════════════════════════════════════════
# ▢ 5a. Show auth working both ways:
#         uv run python src/check_auth.py          (rows fail/succeed
#         as expected — swap in MY_TOOL_NAME for the protected rows
#         if you want it in the table)
# ▢ 5b. Open the run in LangSmith. Find, in order: the fetch_my_data
#       call -> the write_file -> the execute -> the printed numbers.
#       Copy the trace link for your deliverables.
# ▢ 5c. The adversarial poke (04-challenge.md) — run it, then write
#       one sentence: what did it get, and what would have stopped it?
