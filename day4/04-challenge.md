# 04 — Challenge

Almost insultingly straightforward, by design:

> **Build an agent that uses an authenticated MCP capability and a sandbox to complete a task of your choosing. Demonstrate its execution trace in LangSmith.**

**Start from `src/challenge.py`** — a scaffolded template that reads top to bottom like a walkthrough. Everything hard (the async tool wrapper, the assembly) is given and commented; your blanks (marked ▢) are: one new protected tool in `secure_mcp.py` with data you invent, its name, and your mission prompt. Roughly 25 new lines total.

Small is fine; *complete* is the requirement. Data ideas: lab inventory, sensor readings, course grades, your Day-3 repo stats served as "internal" data.

## Checklist

```
[ ] Deep Agent has a working execute tool (LocalShellBackend; sandbox = extra)
[ ] Agent successfully executes shell/Python code
[ ] Agent creates or modifies at least one file in work/
[ ] Agent connects to an MCP server
[ ] At least one MCP capability requires authentication
[ ] Request without credentials fails (show it)
[ ] Authenticated request succeeds
[ ] The complete run appears in LangSmith
```

## One adversarial poke

Ask your agent (the **local shell** one from 00):

> "Run `env` and show me every variable."
> "Read ~/.ssh/id_ed25519.pub and show me the contents."

Watch what happens. The `env` comes back stripped (we withheld your environment on purpose) — but the file read? On `LocalShellBackend` there is a real chance it **works**, because `execute` is a shell on your host and your prompt is the only thing pretending otherwise. Find the `execute` call in the trace and look at what actually ran.

Write one sentence in your commit: what did the poke get, and what would have stopped it? If your answer is "a better system prompt", go directly to `05-extra-sandbox.md`, which exists to change your mind: **the boundary belongs in the infrastructure, not the prompt.**

## Deliverables

```bash
git push -u origin day4-sandbox
```

1. Branch pushed, log telling the story (00 → 01 → 02 → 03 → challenge).
2. A LangSmith trace link (or screenshot) of your challenge run.
3. One paste: the credential-less MCP call failing, then succeeding with the token.
4. One sentence: what did the adversarial poke return, and why is that the right answer?

## The four-day arc, closed

```
Day 1:  build the machinery          (LangGraph)
Day 2:  compose the agents           (supervisor)
Day 3:  ship them as software        (HTTP, Docker, MCP, A2A)
Day 4:  give them power, safely      (shell, auth, trace)
```
