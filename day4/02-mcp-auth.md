# 02 — Authenticated MCP: URL + identity → access

**Edit:** `src/secure_mcp.py` · **Docs:** https://gofastmcp.com/servers/auth/token-verification

Yesterday, knowing your MCP server's URL meant full access. Today:

```
Yesterday:   MCP URL            → access
Today:       MCP URL + identity → access
```

Two words, kept separate on purpose:

```
authentication = who are you?          (the bearer token)
authorization  = what may you access?  (the scopes ON that token)
```

No OAuth today. `StaticTokenVerifier` accepts predefined tokens with attached scopes — a **dev tool** (production verifies real JWTs), but the architecture is identical, and the architecture is what you're learning.

## Your task

In `src/secure_mcp.py` — the whole thing is ~30 lines:

```python
verifier = StaticTokenVerifier(tokens={
    "<student token>": {"client_id": "student", "scopes": ["read:public"]},
    "<admin token>":   {"client_id": "admin",   "scopes": ["read:public", "read:internal"]},
})
mcp = FastMCP("Secure Tools", auth=verifier)

@mcp.tool                                        # public: any valid token
def get_server_time() -> str: ...

@mcp.tool(auth=require_scopes("read:internal"))  # protected
def get_internal_report() -> dict: ...
```

Tokens come from `.env`. Run on port 8002.

## Verify — run the provided matrix script

No async to write: `src/check_auth.py` is **given**, fully commented, and starts with a 60-second async explainer worth actually reading. With your server running:

```bash
uv run python src/check_auth.py
```

| Attempt | Expected |
|---|---|
| no token | **401** at the door |
| wrong token | **401** |
| student token → `get_server_time` | ✅ |
| student token → `get_internal_report` | ❌ — look CLOSELY at the error |
| admin token → `get_internal_report` | ✅ |

That fourth row is the best line of the day: the student doesn't get "forbidden" — they get **`Unknown tool`**. FastMCP filters tools you're not authorized for out of discovery entirely. Authorization doesn't just gate calls; it shapes what you can *see exists*. (401 = authentication failed; `Unknown tool` = authorization at work.)

## ✅ Git checkpoint

```bash
git add day4/src/secure_mcp.py
git commit -m "day4: authenticated MCP with scoped public/protected tools"
```
