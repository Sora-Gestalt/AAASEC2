# 06 — FastMCP: agent ↔ tools, as a protocol

**Edit:** `src/mcp_server.py` · **Docs:** https://gofastmcp.com

## What MCP is (one sentence each)

```
MCP  =  a standard protocol for an AGENT to discover and use TOOLS/RESOURCES
A2A  =  a standard protocol for an AGENT to discover and talk to another AGENT  (09)
```

Until now your tools lived *inside* your Python process — only your agent could use them. An MCP server puts them on the network with a discovery protocol, so *any* MCP-speaking client (Claude Desktop, Cursor, another student's agent, your own code) can list and call them.

## Version note — read this before installing anything

As of today, **stable FastMCP is the 3.x line** (we pin `fastmcp>=3.4,<4` in `pyproject.toml`) — that is what you should use normally. **FastMCP 4 is in beta**, built on the MCP SDK v2 and the new *sessionless* protocol era — that is where MCP is *going*, and it's interesting enough to get its own guide (`08-stateful-vs-stateless.md`). Most ordinary v3 servers carry over essentially unchanged. Course rule: v3 for everything you ship today; v4 for the protocol experiment.

## Your task

In `src/mcp_server.py`, the whole server is ~20 lines of substance:

```python
from fastmcp import FastMCP

mcp = FastMCP("<your-name> Tools")

@mcp.tool
def calculate(expression: str) -> float:
    """Evaluate a basic arithmetic expression, e.g. '2 * (3+4) ** 2'."""
    ...
```

1. Create the server, add **two tools** (`calculate`, `word_stats` — or invent your own; the docstring + type hints *are* the tool's interface, write them like you mean it).
2. Under `__main__`: `mcp.run(transport="http", host="0.0.0.0", port=8001)`.
3. Leave the `SkillsDirectoryProvider` line for `07` — one thing at a time.

## Verify — with an MCP client, not curl

MCP over HTTP is a protocol, not a REST API, so verify with a client:

```bash
uv run python src/mcp_server.py     # terminal 1
```

```python
# terminal 2: uv run python
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:8001/mcp") as c:
        print([t.name for t in await c.list_tools()])
        r = await c.call_tool("calculate", {"expression": "2*(3+4)**2"})
        print(r.data)   # 98.0

asyncio.run(main())
```

Then `docker compose up --build` and verify the same against the composed `mcp` service. Two processes, one application — that's why 05 came first.

*(Wiring these MCP tools INTO your Deep Agent is possible via `langchain-mcp-adapters` — good bonus if you're ahead; not required today.)*

## ✅ Git checkpoint

```bash
git add day3/src/mcp_server.py
git commit -m "day3: serve tools over MCP"
```

→ Continue to `07-skills-over-mcp.md`
