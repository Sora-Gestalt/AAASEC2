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


import os
from pathlib import Path
import ast
import operator
import asyncio
import typing
from datetime import datetime
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

# =====================================================================
# 1. Two Boring Tools
# =====================================================================

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}

def safe_eval_ast(node):
    """Recursively walks an AST node to calculate the mathematical result."""
    # Base Case: Raw number
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    # Binary Operations: e.g. 3 + 4
    elif isinstance(node, ast.BinOp):
        left_val = safe_eval_ast(node.left)
        right_val = safe_eval_ast(node.right)
        op_type = type(node.op)
        if op_type in OPERATORS:
            return OPERATORS[op_type](left_val, right_val)
        raise ValueError(f"Unsupported operator: {op_type.__name__}")

    # Unary Operations: e.g. -5
    elif isinstance(node, ast.UnaryOp):
        operand_val = safe_eval_ast(node.operand)
        op_type = type(node.op)
        if op_type in OPERATORS:
            return OPERATORS[op_type](operand_val)
        raise ValueError(f"Unsupported unary operator: {op_type.__name__}")

    else:
        raise ValueError(f"Forbidden or unsupported syntax: {type(node).__name__}")

@tool
def calculate(expression: str) -> str:
    """Use this tool to evaluate basic arithmetic expressions safely."""
    try:
        parsed_tree = ast.parse(expression, mode="eval")
        # Evaluate node.body (ast.Expression wrapper -> top-level node)
        result = safe_eval_ast(parsed_tree.body)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"

@tool
def current_time() -> str:
    """Use this tool to get the current timestamp."""
    return datetime.now().isoformat()


# =====================================================================
# 2. Fake Agent Fallback (for USE_FAKE=1)
# =====================================================================

class FakeAgent:
    """Mock agent matching the required .ainvoke({"messages": [...]}) contract."""
    async def ainvoke(self, input_data: dict[str, typing.Any]) -> dict[str, typing.Any]:
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": "[FakeAgent response] Hello! I am running in fake mode."
                }
            ]
        }


# =====================================================================
# 3. Agent Builder
# =====================================================================

def build_agent() -> object:
    """Factory satisfying the contract required by api.py."""
    
    # Check if mock mode is requested
    if os.getenv("USE_FAKE", "0") == "1":
        return FakeAgent()

    # OpenRouter LLM setup via ChatOpenAI
    model = ChatOpenAI(
        model="gpt-5.4-nano",
        openai_api_base="https://openrouter.ai/api/v1",
    )

    # Instantiate deep agent with filesystem backend & skills
    agent = create_deep_agent(
        model=model,
        tools=[calculate, current_time],
        system_prompt="You are a helpful assistant equipped with calculation and time tools.",
        backend=FilesystemBackend(root_dir=str(PROJECT_ROOT),virtual_mode=True),
        skills=["./skills/"],
    )
    
    return agent


# =====================================================================
# 4. __main__ Smoke Test
# =====================================================================

async def main():
    agent = build_agent()
    print("Agent initialized successfully.")

    # Turn 1: Test the research skill invocation
    turn1_input = {
        "messages": [
            {
                "role": "user",
                "content": """a code review note on this code
                            def review(code):
                return [
                    rule for rule in [
                        "eval(" in code and "Critical: Avoid eval()",
                        "exec(" in code and "Critical: Avoid exec()",
                        "subprocess" in code and "Warning: Audit shell execution",
                        "secret" in code.lower() and "Warning: Possible hardcoded secret",
                    ] if rule
                ]
                """,
            }
        ]
    }
    response1 = await agent.ainvoke(turn1_input)

    turn1_reply = response1["messages"][-1].content
    print("--- Code Review Notes Reply ---")
    print(turn1_reply)

    # Turn 2: Append follow-up prompt to existing conversation history
    turn2_input = {
        "messages": response1["messages"]
        + [{"role": "user", "content": "What is 15 x 15"}]
    }
    response2 = await agent.ainvoke(turn2_input)

    turn2_reply = response2["messages"][-1].content
    print("\n--- Math Reply ---")
    print(turn2_reply)


if __name__ == "__main__":
    asyncio.run(main())