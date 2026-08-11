# 01 — Deep Agents: the harness you've earned

**Edit:** `src/agent.py` · **Docs:** https://docs.langchain.com/oss/python/deepagents/overview

## From Days 1–2 to today

On Day 1 you wired `StateGraph` nodes by hand. On Day 2 you built a supervisor. Today you call one function:

```python
from deepagents import create_deep_agent

agent = create_deep_agent(model=llm, tools=[...], system_prompt=..., skills=[...])
```

and receive an agent with planning, a virtual filesystem (`ls`/`read_file`/`write_file`/`edit_file`), subagents, memory, and skills — for free. Run `type(agent)` on it: it's a **`CompiledStateGraph`**. Deep Agents is not a new runtime; it is an opinionated harness *on top of the exact machinery you built yourself*. That's why this course taught it last: using the abstraction is trivial once you know what it hides, and dangerous when you don't.

## Backends: what the agent's "filesystem" actually is

| Backend | Filesystem tools | `execute` (shell) | Where files live |
|---|---|---|---|
| `StateBackend` (default) | ✅ | ❌ | LangGraph state, per-thread |
| `FilesystemBackend` | ✅ | ❌ | real disk under `root_dir` |
| `LocalShellBackend` | ✅ | ⚠️ **on your host** | real disk |
| sandbox backends | ✅ | ✅ isolated | sandbox |

We use `FilesystemBackend(root_dir=<day3/>, virtual_mode=True)` so the agent can read `skills/` from disk, confined under the project root.

> **Deep Agents can also execute code when connected to an execution backend. We are NOT doing that today.** Filesystem access ≠ code execution ≠ *safe* code execution. Tomorrow: sandboxes, isolation, permissions, and "what could possibly go wrong?" Until then, `LocalShellBackend` with a real LLM is how today's lab becomes tomorrow's incident report.

## Your task

Open `src/agent.py`. Implement:

1. **Two boring tools** — `calculate(expression)` (AST-walking arithmetic, *not* `eval`) and `current_time()`. Boring is deliberate: today is about everything *around* the agent.
2. **`build_agent()`** — returns the agent. `USE_FAKE=1` returns a `FakeAgent` with the identical `.ainvoke({"messages": [...]})` interface. This function boundary is the first architecture lesson of the day:

```
api.py ──► build_agent() ──► create_deep_agent
                         └── FakeAgent
                         └── (Day 2's supervisor, if you felt like it)
```

Everything downstream — the API, the Dockerfile, the frontend you'll build in a later session — depends on the *boundary*, never the implementation.

3. **Smoke test** under `__main__`.

Model setup is the same OpenRouter `ChatOpenAI` you've used since Day 1 (`:free` suffix, `base_url` override).

## Verify

```bash
USE_FAKE=1 uv run python src/agent.py     # fake reply, instantly
uv run python src/agent.py                # real: should USE the calculate tool
```

Ask it something that *forces* a tool ("what is 17 * 23 and what time is it?"). If it answers from its weights without calling the tool, tighten your system prompt.

## ✅ Git checkpoint

```bash
git add day3/src/agent.py
git commit -m "day3: deep agent behind build_agent() boundary"
```

→ Continue to `02-agent-skills.md`
