"""
DAY 3 — MCP server (SOLUTION).

Two things live here, and keeping them straight is the whole lesson:

  TOOLS      — actions another agent can CALL   (@mcp.tool)
  SKILLS     — knowledge another agent can READ (SkillsDirectoryProvider)

The provider exposes every skill under skills/ as MCP RESOURCES:

  skill://research-brief/SKILL.md
  skill://research-brief/_manifest

MCP transports and discovers the skill. It does NOT execute it. The
agent that downloads a skill interprets SKILL.md with its own tools in
its own runtime — and anything dangerous a skill might want to run
needs an execution boundary, which is exactly Day 4's topic.

Run it:
    uv run python src/mcp_server.py
    # or: uv run fastmcp run src/mcp_server.py:mcp --transport http --port 8001
"""

import ast
import operator as op
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.providers.skills import SkillsDirectoryProvider

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

mcp = FastMCP("AAASEC2 Student Tools")


# ---------- tools: things other agents can DO through us ----------

_ALLOWED = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
    ast.Div: op.truediv, ast.Pow: op.pow, ast.USub: op.neg, ast.Mod: op.mod,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED:
        return _ALLOWED[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED:
        return _ALLOWED[type(node.op)](_safe_eval(node.operand))
    raise ValueError("only basic arithmetic is allowed")


@mcp.tool
def calculate(expression: str) -> float:
    """Evaluate a basic arithmetic expression, e.g. '2 * (3 + 4) ** 2'."""
    return _safe_eval(ast.parse(expression, mode="eval").body)


@mcp.tool
def word_stats(text: str) -> dict:
    """Count words, characters, and lines in a piece of text."""
    return {
        "words": len(text.split()),
        "characters": len(text),
        "lines": text.count("\n") + 1,
    }


# ---------- skills: knowledge other agents can FETCH from us ----------

mcp.add_provider(SkillsDirectoryProvider(roots=SKILLS_DIR))


if __name__ == "__main__":
    # HTTP transport so it's reachable over the network (and from compose).
    mcp.run(transport="http", host="0.0.0.0", port=8001)
