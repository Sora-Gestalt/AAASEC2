# Day 2 Lab — Multi-Agent Research Team (Supervisor Pattern)

Yesterday you built a **single agent**. Today you build a **team**.

```
             ┌──────────── supervisor ─────────────┐
             │       (LLM decides who's next)      │
    ┌────────┼───────────┬───────────┬─────────────┤
    ↓        ↓           ↓           ↓             ↓
 researcher  analyst    writer     critic       FINISH
    │        │           │           │             ↓
    └────────┴───────────┴───────────┘            END
         (every worker reports back to the supervisor)
```

## Day 1 vs Day 2 — the mental model shift

| | Day 1 — single agent | Day 2 — multi-agent |
|---|---|---|
| Nodes | Python functions | LLM **agents** with personas |
| Routing | your `if/else` (`quality_router`) | a supervisor **LLM** decides at runtime |
| Prompts | one prompt for everything | one system prompt **per agent** |
| Tools | available everywhere | **scoped** — only the researcher can search |
| Loop | quality-score retry | critic sends the draft back to the writer |
| Loop safety | `iteration_count` cap | turn cap + revision cap (**guardrails around the LLM**) |
| State | pipeline (fill fields in order) | **blackboard** (agents read all, write their section) |
| Mermaid shape | a chain with one back-edge | a **star** with supervisor at the center |

**What does NOT change:** it's still `StateGraph` + nodes + edges + reducers + a checkpointer. Multi-agent is not a new framework — it's a design pattern on the same primitives you already know.

**When is Day 1's design better?** When the task is a fixed pipeline with a checkable quality bar, a single agent is cheaper, faster, and easier to debug. Multi-agent buys you specialization and dynamic routing — and costs you more LLM calls, more latency, and more failure modes. Coordination must earn its cost. (This question is on the self-check.)

## Files

| File | What it is |
|---|---|
| `day2_lab_skeleton.ipynb` | **Start here.** The lab notebook with TODOs |
| `day2_lab_skeleton.py` | Same skeleton as a plain script (commit this one) |
| `day2_lab_solution.ipynb` / `day2_lab_solution.py` | Reference solution — only after the self-check |
| `Day2.pdf` | Day 2 slides |

## Setup

Identical to Day 1 (see the [Day 1 README](../day1/README.md) for uv, WSL, OpenRouter, and git details):

```bash
cd day2
uv sync                       # or reuse day1's env: uv run --project ../day1 jupyter lab
uv run jupyter lab            # open day2_lab_skeleton.ipynb

# Offline smoke test — watch the critic reject the first draft:
USE_FAKE=1 uv run python day2_lab_solution.py
```

Same keys, same `.env` format, same `USE_FAKE=1` offline mode. In fake mode the critic **rejects the first draft**, so you see the full choreography: research → analyze → write → critique (REVISE) → rewrite → critique (APPROVED) → finish.

## Experiments (do at least one)

1. `MAX_REVISIONS = 0` — what happens to output quality?
2. Delete guardrail (a), make the critic always say REVISE, watch the turn cap save you. Then delete guardrail (b) too — `GraphRecursionError`, an old friend.
3. Give the analyst a terrible persona ("be vague and generic"). How far does the damage spread through the team?

## Version control

Same workflow as Day 1: commit the `.py`, one commit per step, export the notebook with `uv run jupyter nbconvert --to script` if you worked in Jupyter. Your `git log --oneline` is part of the deliverable.
