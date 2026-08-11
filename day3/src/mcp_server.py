"""
DAY 3 — MCP server.

READ FIRST:  ../06-fastmcp.md   then   ../07-skills-over-mcp.md

Do not continue until `uv run python src/mcp_server.py` serves on :8001
and a fastmcp Client can list your tools AND your skill resources.

Keep the two categories straight:
    TOOLS  = actions another agent can CALL   (@mcp.tool)
    SKILLS = knowledge another agent can READ (SkillsDirectoryProvider)

TODO:
  1. mcp = FastMCP("<your-name> Tools")
  2. Two @mcp.tool functions (calculate, word_stats — or your own).
  3. mcp.add_provider(SkillsDirectoryProvider(roots=<path to skills/>))
  4. __main__: mcp.run(transport="http", host="0.0.0.0", port=8001)
"""

# TODO
import ast
import operator
from fastmcp import FastMCP
from pathlib import Path
from fastmcp.server.providers.skills import SkillsDirectoryProvider
# 1. Initialize FastMCP server
mcp = FastMCP("Day3 Tools")
mcp.add_provider(SkillsDirectoryProvider(roots=Path(__file__).parent.parent / "skills"))
# --- AST Arithmetic Helper ---
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

def safe_eval_ast(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")
    elif isinstance(node, ast.BinOp):
        left_val = safe_eval_ast(node.left)
        right_val = safe_eval_ast(node.right)
        op_type = type(node.op)
        if op_type in OPERATORS:
            return OPERATORS[op_type](left_val, right_val)
        raise ValueError(f"Unsupported operator: {op_type.__name__}")
    elif isinstance(node, ast.UnaryOp):
        operand_val = safe_eval_ast(node.operand)
        op_type = type(node.op)
        if op_type in OPERATORS:
            return OPERATORS[op_type](operand_val)
        raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
    else:
        raise ValueError(f"Forbidden syntax: {type(node).__name__}")


# ---------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------

@mcp.tool
def calculate(expression: str) -> float:
    """Evaluate a basic arithmetic expression safely using AST parsing.
    
    Supports +, -, *, /, ** and parentheses.
    Example: '2 * (3+4) ** 2' -> 98.0
    """
    parsed_tree = ast.parse(expression, mode="eval")
    result = safe_eval_ast(parsed_tree.body)
    return float(result)


@mcp.tool
def word_stats(text: str) -> dict:
    """Calculate basic linguistic statistics for a given text input.
    
    Returns word count, character count (with and without spaces), 
    and average word length.
    """
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    char_count_no_spaces = len(text.replace(" ", ""))
    avg_word_len = round(char_count_no_spaces / word_count, 2) if word_count > 0 else 0.0

    return {
        "word_count": word_count,
        "char_count": char_count,
        "char_count_no_spaces": char_count_no_spaces,
        "avg_word_length": avg_word_len,
    }


# ---------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------

if __name__ == "__main__":
    # Serve over HTTP on port 8001
    mcp.run(transport="http", host="0.0.0.0", port=8001)
    