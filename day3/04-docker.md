# 04 — Docker: it works on your laptop. Does it work on mine?

**Edit:** `Dockerfile` (provided — your job is to understand every line, then use it)

Your service currently depends on: your Python version, your `.venv`, your OS packages, your working directory, your luck. A **container image** freezes all of that into one artifact; a **container** is that artifact running as an isolated process. Learn exactly eight words today:

```
Dockerfile   the recipe
image        the frozen result of the recipe (immutable)
container    a running process created from an image
layer        one cached step of the recipe
build context what you COPY from (the day3/ directory)
port         -p host:container — the door you publish
env var      config injected at RUN time, not baked at build time
volume       a directory shared with the host (we don't need one today)
```

## Read the Dockerfile

Open `Dockerfile`. Two lines carry the ideas:

- `COPY pyproject.toml uv.lock* ./` **before** `COPY src/` — dependencies change rarely, code changes constantly; ordering the recipe rare→frequent means edits to `src/` reuse the cached dependency layer. This single trick is the difference between 4-second and 4-minute rebuilds.
- `CMD [...]` vs the `RUN` lines — `RUN` executes at *build* time (baked into the image), `CMD` declares what runs at *container start*. Secrets go in at run time (`--env-file`), never in a `RUN`/`COPY` — layers are archived forever inside the image.

## Build and run

```bash
docker build -t aaasec2-agent .

docker run --rm -p 8000:8000 --env-file .env -e USE_FAKE=1 aaasec2-agent
```

(On the shared server it's `podman build` / `podman run` — identical CLI; see `10-challenge.md` for why.)

From another terminal:

```bash
curl http://localhost:8000/healthz
curl -X POST http://localhost:8000/v1/responses -H 'Content-Type: application/json' -d '{"input":"hi"}'
docker ps          # your container, its port mapping
docker logs <id>   # uvicorn's output lives in the container now
```

## Experiments (do at least the first)

1. Touch `src/api.py` (add a comment), rebuild, time it. Now touch `pyproject.toml`, rebuild, time it. You just *felt* layer caching.
2. Run without `-p 8000:8000` and curl. Connection refused — the process is alive *inside*, but you never published the door.
3. `docker run --rm -it aaasec2-agent bash` and look around: `ls`, `python --version`, `env`. This is the machine you actually deployed.

## ✅ Git checkpoint

```bash
git add day3/Dockerfile
git commit -m "day3: containerize agent API"
```

→ Continue to `05-docker-compose.md`
