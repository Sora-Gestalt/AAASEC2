# 08 — Stateful vs stateless (and why MCP changed)
 
No file to edit. This is a concepts guide with one small experiment. — **where does state live, and who has to remember it?**
 
## Three ideas people constantly blur
 
When someone says "stateless", they might mean any of three different things:
 
```
1. STATELESS REQUEST         Every request carries everything the server
                             needs to handle it. Nothing is assumed from
                             previous requests.
 
2. STATEFUL APPLICATION      State exists — baskets, threads, conversations —
                             but it lives in storage and is addressed by an
                             explicit HANDLE (basket_id=bsk_123).
 
3. STATEFUL TRANSPORT        The CONNECTION itself owns the state. Lose the
   SESSION                   connection, lose the state.
```
 
Notice that (1) and (2) coexist happily: an application can be deeply stateful while every individual request is stateless. The only thing that changes is *how state is addressed* — by an explicit handle in the request, instead of by "whichever connection you happen to be holding open".
 
 
> **Stateless transport does not mean your application can't have state. It means state is addressed by handle, not by connection.**
 
## Why anyone cares: replicas
 
The distinction only starts to hurt when you run more than one copy of your server.
 
**Old model — the session owns the state:**
 
```
client ══ session A ══ server replica 1
                │
                └─ state lives HERE, inside replica 1's memory.
                   The client must forever return to replica 1.
                   ("sticky sessions")
```
 
Sticky sessions make horizontal scaling miserable, for three concrete reasons:
 
- The load balancer must pin each client to one replica, instead of routing freely.
- If a replica dies, every session it held dies with it.
- An overloaded replica can't shed clients — they're stuck to it.
**Modern model — state behind an explicit handle:**
 
```
request 1 ── basket_id=bsk_123 ──► replica 1   creates state in shared
                                               storage, returns the handle
request 2 ── basket_id=bsk_123 ──► replica 7   looks the handle up —
                                               any replica will do
```
 
Now the state lives in shared storage (a database, a checkpointer), and the handle in each request tells any replica where to find it. Replicas become interchangeable.
 
You already built this pattern without noticing. LangGraph's `thread_id` from Days 1–2 **is** a state handle: your conversation is stateful (concept 2), but every request that names its `thread_id` is a stateless request (concept 1). No sticky session anywhere.
 
## MCP's version of this story
 
MCP walked exactly this path, in two eras:
 
| | Handshake era (e.g. `2025-11-25`) | Sessionless era (`2026-07-28`) |
|---|---|---|
| Session | `initialize` handshake, then a held session | No protocol-level session |
| Connection | Long-lived; server can push requests back down it | Fresh connection per request |
| Capabilities | Exchanged during the handshake | Discovered via `server/discover` |
| Server state | Session-scoped state is legal | State is *your application's* job, via handles |
| Scaling | Sticky — the session pins you to a replica | Any replica can serve the next request |
 
**FastMCP 4** (beta, built on MCP SDK v2) serves *both eras from the same server* and negotiates per client:
 
- `Client(url)` defaults to `mode="auto"` — negotiate the newest era both sides support.
- `Client(url, mode="legacy")` forces the old handshake era.
## The experiment (~15 min)
 
Run your v3 server from lessons 06/07 as-is, then poke it with a **v4 client**. Use an isolated environment so you don't touch your project's pinned FastMCP v3:
 
```bash
uv run --with "fastmcp==4.0.0b1" --no-project python - <<'EOF'
import asyncio
from fastmcp import Client
 
async def probe(mode):
    async with Client("http://localhost:8001/mcp", mode=mode) as c:
        tools = await c.list_tools()
        print(f"mode={mode!r:8} -> {len(tools)} tools:", [t.name for t in tools])
 
async def main():
    await probe("auto")      # negotiates the newest era both sides speak
    await probe("legacy")    # forces the old handshake era
 
asyncio.run(main())
EOF
```
 
Expected result: **both modes list the same tools.** One server, two protocol eras, negotiated per client.
 
Then answer these two questions — as a comment in your notes or in your commit message:
 
1. In the sessionless era there is no `initialize` handshake, and no state persists between calls at the protocol level. If your v3 server kept per-session state, where must that state move to? *(Hint: you answered this two days ago with `thread_id`.)*
2. Why does the sessionless design make the *shared class server* in `10-challenge.md` easier to operate? Think in terms of replicas and what happens when one restarts.
## ✅ Git checkpoint
 
```bash
git commit --allow-empty -m "day3: v4 protocol probe — state handles > sticky sessions because <your answer>"
```
 
→ Continue to `09-a2a.md`
 
