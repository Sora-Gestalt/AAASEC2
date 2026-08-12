# 00 — Deep Agent + shell: the `execute` tool appears

**Edit:** `src/shell_agent.py` · **Docs:** https://docs.langchain.com/oss/python/deepagents/backends

Yesterday's promise, kept. The difference is exactly one tool:

```
Day 3 agent                Day 4 agent
├── ls                     ├── ls
├── read_file              ├── read_file
├── write_file             ├── write_file
├── edit_file              ├── edit_file
└── ...                    ├── ...
                           └── execute        ← a real shell
```

Today it's `LocalShellBackend`: the shell is **your machine**. Read that twice.

```
⚠  LocalShellBackend has NO isolation. Commands run as your user,
   on your host. We use it today with eyes open, in a lab, on a
   throwaway task — and the challenge will show you exactly why
   you'd never hand this to an untrusted prompt.
```

Two mitigations we set (and one honest admission):

- `root_dir=day4/work/ + virtual_mode=True` — the *file tools* are confined under `work/`;
- `env={"PATH": ...}` — the shell does **not** inherit your environment, so your API keys aren't sitting in `env` for any executed command to read;
- admission: mitigations are not isolation. `execute` is still a shell on your host. The actual fix is a rented computer — `05-extra-sandbox.md`.

## Your task

In `src/shell_agent.py`:

```python
from deepagents.backends import LocalShellBackend

backend = LocalShellBackend(root_dir=str(WORK_DIR), virtual_mode=True,
                            env={"PATH": os.environ["PATH"]})
agent = create_deep_agent(model=llm, system_prompt=..., backend=backend)
```

Then give it this task and watch:

> 1. Create `calculator.py` with add/sub/mul/div (div raises on zero). 2. Write pytest tests including the zero case. 3. Run them with execute (`python -m pytest`; pip install pytest first if missing). 4. Fix failures until green. 5. Report the final pytest output.

You are no longer watching an agent *call functions*. You are watching it *manipulate an environment*: write → run → read the error → fix → re-run. That loop is the thing. When it finishes, `ls work/` — the files are really there, on your disk. Sit with that for a second too.

## ✅ Git checkpoint

```bash
git add day4/src/shell_agent.py
git commit -m "day4: deep agent with shell execution (local, eyes open)"
```
