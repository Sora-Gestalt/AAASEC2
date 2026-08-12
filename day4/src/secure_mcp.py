"""
DAY 4 — Authenticated MCP server.

READ FIRST:  ../02-mcp-auth.md

Do not continue until: no token -> 401, student token -> public tool
works, admin token -> protected tool works.

TODO:
  1. StaticTokenVerifier with two tokens (from .env):
       student -> scopes ["read:public"]
       admin   -> scopes ["read:public", "read:internal"]
  2. mcp = FastMCP("...", auth=verifier)
  3. get_server_time()  — plain @mcp.tool (any valid token)
  4. get_internal_report() — @mcp.tool(auth=require_scopes("read:internal"))
  5. __main__: mcp.run(transport="http", host="0.0.0.0", port=8002)

LATER (04-challenge.md): you'll add ONE more protected tool here that
serves data you invent — same decorator, same scope, different data.
"""

# TODO
