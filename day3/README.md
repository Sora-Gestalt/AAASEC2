# Day 3 — Agents as Networked Software

Days 1–2 taught agent *frameworks*: you built the graph machinery yourself, then composed agents into a supervised team. Today the course changes character. **You will not build a fancier graph.** You will take an agent and turn it into what agents actually are in production: a versioned, containerized, discoverable network service that other agents can find and use.

```
Day 1:  build the machinery yourself        (LangGraph, your router)
Day 2:  compose agents yourself             (supervisor pattern)
Day 3:  use the higher-level harness —      (Deep Agents)
        because you now understand what it hides —
        and ship it as real software        (Git, HTTP, Docker, MCP, A2A)
```

## No notebooks today

Day 3 is files, processes, ports, containers, and commits. A notebook would hide exactly the things being taught. You will work in `src/*.py` with your editor and terminal, and **Git is the spine of the day** — every section ends with a commit, and your `git log` at the end of the day is a deliverable.

## The map

Work through the numbered guides in order. Each one tells you what to build, which `src/` file to edit, and ends with a Git checkpoint.

| Guide | You build | New vocabulary |
|---|---|---|
| `00-git-and-forks.md` | your day-3 branch, upstream sync | working tree, index, HEAD, remotes, reflog |
| `01-deep-agents.md` | `src/agent.py` | harness, backends, filesystem tools ≠ shell |
| `02-agent-skills.md` | `skills/<yours>/SKILL.md` | progressive disclosure, prompt vs skill vs tool |
| `03-fastapi-openresponses.md` | `src/api.py` | API contract ≠ agent implementation |
| `04-docker.md` | `Dockerfile`, an image | image, container, layer, port, env |
| `05-docker-compose.md` | `compose.yaml` | services, compose network, service DNS |
| `06-fastmcp.md` | `src/mcp_server.py` | MCP: agent ↔ tools |
| `07-skills-over-mcp.md` | skills as MCP resources | transporting knowledge ≠ executing it |
| `08-stateful-vs-stateless.md` | a v4 protocol experiment | state handles, sticky sessions, why v4 |
| `09-a2a.md` | agent card + `src/a2a_client.py` | A2A: agent ↔ agent, discovery |
| `10-challenge.md` | delegation across the class network | the point of all of the above |

The end state, per student:

```
                 Internet / class network
                          │
                 ┌────────▼─────────┐
                 │  your instance    │
                 │  (podman compose) │
                 │  ┌─────────────┐  │
     HTTP ───────┼──► FastAPI     │  │   /healthz
                 │  │ OpenResponses│ │   /v1/responses
                 │  └──────┬──────┘  │   /.well-known/agent-card.json
                 │         │         │
                 │    Deep Agent     │   tools + skills, NO shell (Day 4)
                 │         │         │
                 │  ┌──────▼──────┐  │
                 │  │ FastMCP     │  │   tools + skill:// resources
                 │  └─────────────┘  │
                 └────────┬──────────┘
                          │ A2A discovery + delegation
                          ▼
                  another student's agent
```

## Setup (5 min)

```bash
git switch -c day3-api          # everything today happens on this branch (see 00-*.md)
cd day3
uv sync
cp .env.example .env            # add your OpenRouter key; set STUDENT_NAME
```

No key? `USE_FAKE=1` runs a deterministic fake agent — the *entire* HTTP/Docker/compose/A2A pipeline still works, which is most of today. Same OpenRouter setup as Day 1 (`day1/README.md`).

The `solutions/` folder contains reference implementations of every `src/` file. Same rule as always: TODOs first, solutions after you're stuck for real.

## What is deliberately NOT here

Code execution and sandboxes. Deep Agents *can* execute code when connected to an execution backend. **We are not doing that today.** Tomorrow: agents writing code, agents executing code, isolation, permissions, resource limits, and "what could possibly go wrong?"
