"""
DAY 4 — Deep Agent with shell access.

READ FIRST:  ../00-deep-agent-shell.md

TODO:
  1. llm — same OpenRouter ChatOpenAI as every day.
  2. make_backend() -> (backend, cleanup_fn). Default "local":
       LocalShellBackend(root_dir=<day4/work/>, virtual_mode=True,
                         env={"PATH": os.environ["PATH"]})
       cleanup = nothing (it's your host)
     EXTRA (05-extra-sandbox.md): "daytona" -> Daytona().create()
       + DaytonaSandbox, cleanup = sandbox.stop
  3. __main__: create backend, create_deep_agent(model, system_prompt,
     backend=backend), invoke the calculator task, print the reply,
     cleanup in a finally block.
"""

# TODO
