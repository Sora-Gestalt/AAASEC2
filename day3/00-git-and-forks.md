# 00 — Git, your fork, and the branch you'll live on today

No hypothetical Alice-and-Bob editing `hello.txt`. Your **actual topology**, right now:

```
            upstream
     snow10100/AAASEC2  (the course repo)
              │  GitHub fork
              ▼
     <you>/AAASEC2      (origin — YOUR repo)
              │  git clone
              ▼
      your laptop / WSL
```

## 1. Inspect what you have

```bash
git remote -v          # probably only "origin" → your fork
git branch             # probably only "main"
git status
git log --oneline --graph --decorate --all
```

Run each. Read the output. Seriously — the difference between people who "know Git" and people who fear it is the habit of *looking* before typing.

## 2. Wire up upstream and sync

Your fork does not update itself when the course repo changes. Connect it:

```bash
git remote add upstream git@github.com:snow10100/AAASEC2.git
git remote -v          # now two remotes

git fetch upstream
git switch main
git merge --ff-only upstream/main   # fast-forward: your main = course main
git push origin main
```

`--ff-only` refuses to merge if you've committed to `main` directly (you shouldn't have — see next step). If it refuses, ask an instructor; that's a teachable moment, not a crisis.

## 3. The mental model (this is 80% of Git)

```
working tree            the files you edit
     │  git add
staging area / index    the snapshot you're COMPOSING
     │  git commit
repository (HEAD)       history on your machine
     │  git push
origin                  history on GitHub
```

Every confusing Git situation is just a question of *which of these four places* a change currently lives in. `git status` tells you.

## 4. Create today's branch

```bash
git switch -c day3-api
```

**Everything you build today happens on this branch.** Commit early, commit small — one commit per completed guide is the minimum; one per meaningful step is better. Your end-of-day `git log --oneline` should read like this day's table of contents.

## 5. Survival kit (read now, thank yourself later)

```bash
git restore file.py            # discard uncommitted edits to a file
git restore --staged file.py   # un-add (keep the edits, unstage them)
git revert <commit>            # undo a commit WITH a new commit (safe, shareable)
git reflog                     # the command you remember when you think
                               # you've destroyed your repository
```

Git is bizarrely difficult to permanently murder, despite its UI constantly suggesting otherwise. `reflog` records where HEAD *was*, including states you think you've lost.


## ✅ Git checkpoint

```bash
git status                      # clean? on day3-api?
git commit --allow-empty -m "day3: start of lab (branch created, upstream wired)"
```

→ Continue to `01-deep-agents.md`
