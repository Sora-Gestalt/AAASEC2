# 01 — LangSmith: from print() to seeing what actually happened

**Edit:** nothing. That's the lesson.

Yesterday you debugged with `print()` and `docker logs`. Today your agent runs a multi-step loop inside a remote sandbox — printing your way through that is misery. Tracing is on the moment these are in your `.env` (they already are, from setup):

```
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=aaasec2-day4
```

Zero code changes. LangChain/LangGraph instruments itself.

## Your task

Re-run the calculator task from 00. Open https://smith.langchain.com → your project → the run. You'll see something shaped like:

```
trace
├── user message
├── model call
├── tool: write_file (calculator.py)
├── model call
├── tool: write_file (test_calculator.py)
├── model call
├── tool: execute ("pip install pytest && pytest")
├── model call            ← read the output here
└── final answer
```

Answer **three questions from the trace** (put the answers in your commit message):

1. How many model calls did the run make?
2. Which tools were invoked, in what order?
3. Find the moment the agent recovered from an error (a failing test, a missing package). What did it read, and what did it change?

If your run went green on the first try, break it on purpose — tell the agent to write one deliberately failing test first — so there's a recovery to find.

That's it. Tracing is a *debugging tool you reach for*, not a dashboard you ceremonially admire. The through-line since Monday: Day 1 streamed graph state, Day 2 inspected routing, Day 3 inspected services, Day 4 inspects the complete execution trace.

## ✅ Git checkpoint

```bash
git commit --allow-empty -m "day4: traced run — <N> model calls, tools: <...>, recovery at <...>"
```
