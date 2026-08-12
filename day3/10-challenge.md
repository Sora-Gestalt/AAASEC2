# 10 — Challenge: the room becomes a multi-agent system

Everything so far was solo. Now:

> **Build one genuinely useful capability into your agent (skill or tool), deploy your stack to your instance on the shared server, then DISCOVER another student's Agent Card and DELEGATE a real task to their agent.** Bonus: download a skill from their MCP server and make your agent use it.

```
              A2A                                A2A
 student A ◄──────► student B      student C ◄──────► student D
    │                  │               │                  │
   MCP                MCP             MCP                MCP
    │                  │               │                  │
 tools A            tools B         tools C            tools D
```

## Your instance

You each get a slot on the shared server, provisioned from your GitHub fork:

```
GitHub username ──► your public SSH keys (github.com/<user>.keys)
       ──► you CONFIRM which key (or better: a course-specific one)
       ──► authorized_keys on your slot
```

Make a course-specific key so access is cleanly revocable afterwards:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/aaasec2 -C "aaasec2-course"
# add ~/.ssh/aaasec2.pub to your GitHub account, tell the instructor it's ready
ssh -i ~/.ssh/aaasec2 <you>@<server>
```

**On the server, `docker` is `podman`.** Same CLI (`podman build`, `podman compose up -d`), but rootless: your containers run as *your* user, no shared root daemon, no docker group that's root-equivalent — thirty students on one box is precisely the scenario rootless exists for. Ports are assigned per student (check the port sheet); set them in your compose file and your `.env`:

```
STUDENT_NAME=<your-github-username>
PUBLIC_URL=http://<server>:<your-api-port>
```

## Deploy

```bash
ssh -i ~/.ssh/aaasec2 <you>@<server>
git clone git@github.com:<you>/AAASEC2.git && cd AAASEC2
git switch day3-api
cd day3 && cp .env.example .env   # fill in key, name, PUBLIC_URL, ports
podman compose up -d --build
curl http://localhost:<your-api-port>/healthz
```

Post your base URL in the WhatsApp group. Then:

```bash
uv run python src/a2a_client.py http://<server>:<their-port> "<a task their card says they're good at>"
```

Read their card FIRST and send a task that matches their advertised skills — that's the protocol working, not a party trick.

## Deliverables (end of day)

1. Your stack up on your instance, `/healthz` green, card served.
2. A screenshot/paste of your client discovering + delegating to **another student's** agent, and their agent's reply.
3. Your branch pushed, with a log that tells the day's story:

```bash
git push -u origin day3-api
git log --oneline --graph --decorate
```

Expected shape:

```
a1b2c3d day3: agent card + A2A discovery client
…       day3: expose agent skills over MCP
…       day3: serve tools over MCP
…       day3: run services with compose
…       day3: containerize agent API
…       day3: expose agent through FastAPI (OpenResponses subset)
…       day3: add <your-skill> agent skill
…       day3: deep agent behind build_agent() boundary
```

If your log looks like one giant `day3: everything` commit — that, too, is feedback.

## The vocabulary you leave with

```
OpenResponses = user/client ↔ agent API
MCP           = agent ↔ capabilities/context
Agent Skills  = reusable procedural knowledge
A2A           = agent ↔ agent
Docker/podman = package & run the services
Compose       = run the services TOGETHER
Git           = track how you created this mess
Sandbox       = tomorrow.
```
