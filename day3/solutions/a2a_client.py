"""
DAY 3 — A2A discovery + delegation client (SOLUTION).

Usage:
    uv run python src/a2a_client.py http://<peer-host>:<port> "Write a research brief on quadrotors"

What it does — the two halves of agent-to-agent interaction:

  1. DISCOVER  GET  {peer}/.well-known/agent-card.json
               "who are you, what can you do, where do I reach you?"
  2. DELEGATE  POST {card.url}   (their OpenResponses endpoint)
               "do this task for me"

Note the client never hardcodes the peer's chat endpoint — it reads it
from the card. That indirection IS the protocol: discovery decouples
"I know where you live" from "I know how to use you".

(The full A2A task protocol via the official `a2a-sdk` — task ids,
lifecycle states, streaming — is the bonus in 09-a2a.md.)
"""

import json
import sys

import httpx


def discover(peer_base_url: str) -> dict:
    url = peer_base_url.rstrip("/") + "/.well-known/agent-card.json"
    card = httpx.get(url, timeout=10).raise_for_status().json()
    print(f"── discovered: {card['name']} (v{card.get('version', '?')})")
    print(f"   {card.get('description', '')}")
    for skill in card.get("skills", []):
        print(f"   • {skill['name']}: {skill['description']}")
    return card


def delegate(card: dict, task: str) -> str:
    endpoint = card["url"]  # from the card — never hardcoded
    print(f"── delegating to {endpoint} ...")
    resp = httpx.post(endpoint, json={"input": task}, timeout=120).raise_for_status().json()
    for item in resp.get("output", []):
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "output_text":
                    return part["text"]
    raise ValueError(f"no output_text in response: {json.dumps(resp)[:300]}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    peer, task = sys.argv[1], sys.argv[2]
    card = discover(peer)
    answer = delegate(card, task)
    print("\n── their agent replied:\n")
    print(answer)
