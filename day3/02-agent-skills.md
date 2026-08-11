# 02 — Agent Skills: procedural knowledge as files

**Edit:** `skills/<your-skill>/SKILL.md` · **Spec:** https://agentskills.io/skill-creation/quickstart

## Four words that must not blur together

```
PROMPT    "what should you do?"          (identity + goals)
SKILL     "HOW do you do this KIND of task?"  (reusable procedure)
TOOL      "what action can you perform?" (a callable capability)
SANDBOX   "where may dangerous execution happen?"  (Day 4)
```

A skill is just a folder with a `SKILL.md`:

```
skills/
└── research-brief/
    └── SKILL.md        <- frontmatter (name, description) + instructions
```

Open `skills/research-brief/SKILL.md` — that's the whole format. Frontmatter for discovery, body for procedure.

## Progressive disclosure — the actual idea

The agent does **not** load every skill into context at startup. It sees only each skill's `name` + `description` (cheap). When a request matches, it loads the full `SKILL.md` (expensive) and follows it. Discovery is cheap; activation is on demand. This is how you give an agent fifty procedures without burning fifty procedures' worth of tokens on "hello".

The open Agent Skills format works across compatible runtimes — Deep Agents reads it natively (`skills=["/skills/"]`), and this afternoon you'll serve the *same folder* over MCP untouched.

## Your task

1. **Test the provided skill.** Ask your agent (from 01) for "a research brief on aerial manipulation". Verify the output follows the skill's structure — headline, exactly three findings, confidence line. Then ask something unrelated ("what's 2+2?") and confirm the skill *didn't* activate. That contrast is progressive disclosure working.
2. **Write your own skill.** Make it something *you* would actually reuse: `commit-message` (write conventional commits from a diff description), `code-review-notes`, `bug-report`, `lab-report-kfupm` — your call. Rules of a good SKILL.md:
   - the `description` is what triggers discovery — write it like a docstring for a router;
   - the body gives a *checkable* procedure (structure, limits, forbidden phrases), not vibes;
   - keep it under a page. Skills that ramble get half-followed.
3. **Test yours** the same way: one prompt that should trigger it, one that shouldn't.

A skill *may* also ship `scripts/` — but merely having a script grants no execution rights. The agent can *read* `scripts/analyze.py` with its filesystem tools today; *running* it requires an execute tool, which requires a sandbox, which is Day 4. Sit with that chain for a second — it's the whole security model in one sentence:

```
SKILL.md → agent understands procedure → needs to run a script
        → needs execute → execute needs a boundary → SANDBOX
```

## ✅ Git checkpoint

```bash
git add day3/skills/
git commit -m "day3: add <your-skill> agent skill"
```

→ Continue to `03-fastapi-openresponses.md`
