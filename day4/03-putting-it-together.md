# 03 — Putting it together: one mission, three pieces

**Edit:** `src/mission.py` · needs `src/secure_mcp.py` running in another terminal

```
                  LangSmith
                     ▲  traces
                     │
User ──► Deep Agent ─┤
           │         │
           │ tool    │ backend
           ▼         ▼
 Authenticated MCP  Sandbox
```

The mission:

> Fetch the quarterly data from the **protected** MCP tool, write a Python analysis program **in your work/ dir via the agent**, **execute** it, and report totals + profit margin — then read the whole thing back **in the trace**.

Each piece contributes one thing and can't be faked:

```
MCP        →  information   (it's behind auth — no token, no data)
shell      →  computation   (analyze.py is written and executed BY the agent, not by you)
LangSmith  →  visibility    (you can point at every step after the fact)
```

## Your task

In `src/mission.py`:

1. Read `fetch_internal_report()` — it is **given** in the skeleton, fully commented, because it's the only async code today and you shouldn't have to invent async under time pressure. Sync outside, async inside, `asyncio.run` as the single bridge (rules in `src/check_auth.py`'s explainer). To the agent it's just another tool; the network protocol and the bearer token are hidden inside. (Where have you seen that trick? `build_agent()` — same boundary idea, one level down.)
2. Your actual TODO is ~8 sync lines under `__main__`: build the shell agent from 00 with `tools=[fetch_internal_report]`, invoke `MISSION`, print, cleanup.
3. Run the mission. Then open the trace and find, in order: the MCP fetch → the `write_file` of analyze.py → the `execute` → the numbers coming back.

If the numbers in the final answer don't match what analyze.py printed in the trace, the model summarized instead of computing. Tighten the prompt ("report exactly what the program printed") and re-run — a very Day-4 bug to catch, and you caught it *because* of the trace.

## ✅ Git checkpoint

```bash
git add day4/src/mission.py
git commit -m "day4: mission — protected MCP data analyzed in sandbox, traced"
```
