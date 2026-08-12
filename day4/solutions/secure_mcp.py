"""
DAY 4 — Authenticated MCP server (SOLUTION).

Yesterday:  MCP URL            -> access
Today:      MCP URL + identity -> access

    authentication = who are you?        (the bearer token)
    authorization  = what may you access? (the scopes on that token)

StaticTokenVerifier is a DEV tool: predefined tokens, no infrastructure.
Fine for a lab; in production you'd verify real JWTs. The architecture
is identical either way — that's the point.

Run:  uv run python src/secure_mcp.py     (port 8002)
"""

import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth import require_scopes
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

load_dotenv()

verifier = StaticTokenVerifier(
    tokens={
        os.getenv("MCP_STUDENT_TOKEN", "student-secret-token"): {
            "client_id": "student",
            "scopes": ["read:public"],
        },
        os.getenv("MCP_ADMIN_TOKEN", "admin-secret-token"): {
            "client_id": "admin",
            "scopes": ["read:public", "read:internal"],
        },
    }
)

mcp = FastMCP("AAASEC2 Secure Tools", auth=verifier)


@mcp.tool
def get_server_time() -> str:
    """Current UTC time. Public: any valid token can call this."""
    return datetime.now(timezone.utc).isoformat()


@mcp.tool(auth=require_scopes("read:internal"))
def get_internal_report() -> dict:
    """Quarterly numbers. Protected: requires the read:internal scope."""
    return {
        "quarter": "Q3-2026",
        "revenue_sar": [412_000, 385_000, 505_000],
        "costs_sar": [298_000, 310_000, 342_000],
        "note": "internal only — do not redistribute",
    }


@mcp.tool(auth=require_scopes("read:internal"))
def get_lab_inventory() -> dict:
    """Lab stock. Protected: example of the tool students add in the challenge."""
    return {
        "items": [
            {"name": "TS101 iron", "qty": 4, "unit_cost_sar": 320},
            {"name": "ESC 45A", "qty": 12, "unit_cost_sar": 95},
            {"name": "LiPo 4S", "qty": 7, "unit_cost_sar": 210},
        ]
    }


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8002)
