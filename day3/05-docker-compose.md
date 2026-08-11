# 05 — Docker Compose: the application is now SERVICES

**Edit:** `compose.yaml` (provided — understand it, run it, break it, fix it)

The motivation is not "Compose is YAML with services". The motivation is: **we are about to want more than one process.** In `06-fastmcp.md` you'll add an MCP server next to your API. Two processes, two ports, one lifecycle, config for each — managing that by hand with two terminals and two `docker run` incantations gets old in exactly one afternoon.

```
compose.yaml
├── agent-api   :8000    (FastAPI + Deep Agent)
└── mcp         :8001    (FastMCP — tools + skills)
```

Note what we deliberately did **not** add: Redis, Postgres, a message queue. You'll add persistent state when the course needs persistent state. Humans have destroyed enough systems through premature databases.

## Read compose.yaml, then run it

Three things to notice in the file:

1. Both services `build: .` from the **same image** — different `command` per service. One artifact, many roles.
2. `MCP_URL=http://mcp:8001/mcp` — inside the compose network, services address each other **by service name**. Compose runs DNS for you; `localhost` inside a container means *that container*, not your machine. This bites everyone exactly once. Let it be today.
3. `depends_on` orders *startup*, not *readiness* — mcp's process starts first, but nothing waits for it to be ready. (What would? A healthcheck. Note the idea; we return to it on the shared server.)

```bash
docker compose up --build        # podman compose on the shared server
```

From another terminal:

```bash
curl http://localhost:8000/healthz
curl http://localhost:8001/mcp   # will 4xx politely until 06 is done — that's fine, port is alive
docker compose ps
docker compose logs -f agent-api
```

`Ctrl-C` stops the foreground run; `docker compose up -d` + `docker compose down` is the detached lifecycle.

## ✅ Git checkpoint

```bash
git add day3/compose.yaml
git commit -m "day3: run services with compose"
```

→ Continue to `06-fastmcp.md`
