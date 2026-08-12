"""
DAY 4 — Auth check script (PROVIDED — nothing to write, just run it).

    uv run python src/check_auth.py

It runs the full auth matrix against your secure MCP server (port 8002)
and prints a ✅/❌ table. Your job is to READ the output and the code,
not to write async code.

────────────────────────────────────────────────────────────────────
ASYNC IN 60 SECONDS (read once, then it stops being scary)
────────────────────────────────────────────────────────────────────
The MCP client talks over the network. Network calls are SLOW compared
to CPU work, so the client is written with `async def` — functions that
can PAUSE at every `await` while data travels, instead of blocking.

Three rules cover everything in this course:

  1. `async def f()` defines a coroutine. CALLING it does nothing yet —
     f() just creates the coroutine object.
  2. Inside another async function you run it with `await f()`.
  3. From NORMAL (sync) code, you start the async world with ONE call:
     `asyncio.run(f())` — it runs the coroutine to completion and
     hands you back a plain return value. Sync world resumes.

  `async with Client(...) as c:` is a context manager (like `with
  open(...)`) that happens to need awaiting: it opens the connection
  on entry and cleans it up on exit, even on errors.

That's it. Every async line below is one of those three rules.
────────────────────────────────────────────────────────────────────
"""

import asyncio
import os

from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.auth import BearerAuth

load_dotenv()

URL = os.getenv("MCP_URL", "http://localhost:8002/mcp")
STUDENT = os.getenv("MCP_STUDENT_TOKEN", "student-secret-token")
ADMIN = os.getenv("MCP_ADMIN_TOKEN", "admin-secret-token")


async def attempt(label: str, token: str | None, tool: str) -> None:
    """Try one (token, tool) combination and print what happened."""
    # BearerAuth simply puts "Authorization: Bearer <token>" on every
    # request. token=None means we send no credentials at all.
    auth = BearerAuth(token=token) if token else None
    try:
        # Rule 3's context-manager cousin: open connection, use it, close it.
        async with Client(URL, auth=auth) as client:
            result = await client.call_tool(tool, {})          # rule 2
            print(f"  ✅ {label:34} -> {str(result.data)[:48]}")
    except Exception as e:
        # Both rejections land here. Read the message:
        #   401 Unauthorized  -> authentication failed (who are you?)
        #   Unknown tool      -> authorization failed  (you can't even
        #                        SEE tools your scopes don't allow!)
        print(f"  ❌ {label:34} -> {type(e).__name__}: {str(e)[:60]}")


async def main() -> None:
    print(f"auth matrix against {URL}\n")
    await attempt("no token, public tool", None, "get_server_time")
    await attempt("wrong token, public tool", "not-a-real-token", "get_server_time")
    await attempt("student token, public tool", STUDENT, "get_server_time")
    await attempt("student token, PROTECTED tool", STUDENT, "get_internal_report")
    await attempt("admin token, PROTECTED tool", ADMIN, "get_internal_report")
    print(
        "\nexpected: rows 1-2 rejected at the door (401 = authentication),\n"
        "row 4 rejected as 'Unknown tool' (scopes = authorization — the\n"
        "tool is hidden from you, not just refused), rows 3 and 5 succeed."
    )


if __name__ == "__main__":
    asyncio.run(main())  # rule 3: the ONE bridge from sync to async
