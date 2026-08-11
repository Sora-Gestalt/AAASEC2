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
