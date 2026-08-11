# 07 — Skills over MCP: your knowledge, discoverable

**Edit:** `src/mcp_server.py` (one line!) · **Docs:** https://gofastmcp.com/servers/providers/skills

This morning you wrote a skill. It exists on your machine. One line makes it discoverable and downloadable by any MCP client on the network:

```python
from pathlib import Path
from fastmcp.server.providers.skills import SkillsDirectoryProvider

mcp.add_provider(SkillsDirectoryProvider(roots=Path(__file__).parent.parent / "skills"))
```

Your skills now appear as MCP **resources**:

```
skill://research-brief/SKILL.md      the skill itself
skill://research-brief/_manifest     files, sizes, hashes
skill://<your-skill>/SKILL.md        the one YOU wrote in 02
```

## The distinction to hammer in

The Skills Provider does **not** mean "the server executes this skill remotely". The flow is:

```
MCP server  ── exposes ──► skill resources
                              │ client retrieves
                              ▼
                           agent  ── interprets SKILL.md ──► its OWN tools / sandbox
```

**MCP transports and discovers the knowledge. The receiving agent's runtime decides to activate it. The execution environment runs anything dangerous.** Three different responsibilities, three different places — keep them separate in your head and you already understand half of Day 4.

## Verify

```python
import asyncio
from fastmcp import Client
from fastmcp.utilities.skills import download_skill

async def main():
    async with Client("http://localhost:8001/mcp") as c:
        print([str(r.uri) for r in await c.list_resources()])
        content = await c.read_resource("skill://research-brief/SKILL.md")
        print(content[0].text[:200])
        # pull a whole skill folder down, like another agent would:
        path = await download_skill(c, "research-brief", "/tmp/pulled-skills")
        print("downloaded to", path)

asyncio.run(main())
```

Yesterday that skill was a file on your laptop. It is now a versioned, hash-manifested artifact another agent can discover and install. In `10-challenge.md`, other students will do exactly that to *your* server — make your skill worth downloading.

## ✅ Git checkpoint

```bash
git add day3/src/mcp_server.py
git commit -m "day3: expose agent skills over MCP"
```

→ Continue to `08-stateful-vs-stateless.md`
