"""
DAY 3 — Agent implementation.

READ FIRST:  ../01-deep-agents.md

Do not continue to api.py until:
    USE_FAKE=1 uv run python src/agent.py
prints a reply, AND (with real keys) the agent answers using its tools.

The contract this file must satisfy — the ONLY thing api.py will rely on:

    def build_agent() -> object with .ainvoke({"messages": [...]})

TODO:
  1. Two boring tools: calculate(expression) and current_time().
     (Boring is the point. Day 3 is about everything AROUND the agent.)
  2. build_agent():
       - if USE_FAKE: return a FakeAgent with the same .ainvoke shape
       - else: create_deep_agent(model=<ChatOpenAI via OpenRouter>,
                                 tools=[...], system_prompt=...,
                                 backend=FilesystemBackend(root_dir=<day3/>,
                                                           virtual_mode=True),
                                 skills=["/skills/"])
  3. A __main__ smoke test that invokes the agent once and prints the reply.

NOTE: default backends give the agent FILESYSTEM tools but NO shell.
An execute tool requires a sandbox backend — that is Day 4, on purpose.
"""

# TODO
