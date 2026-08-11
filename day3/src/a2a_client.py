"""
DAY 3 — A2A discovery + delegation client.

READ FIRST:  ../09-a2a.md
USED IN:     ../10-challenge.md

Usage:
    uv run python src/a2a_client.py http://<peer> "task for their agent"

TODO:
  1. discover(peer_base_url) -> GET {peer}/.well-known/agent-card.json,
     print the card's name + skills, return the card dict.
  2. delegate(card, task) -> POST to card["url"] (NEVER hardcode the
     endpoint — read it from the card; that indirection IS the protocol)
     and extract the output_text from the OpenResponses reply.
  3. __main__ wiring the two together from sys.argv.
"""

# TODO
