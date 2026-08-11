import asyncio
from fastmcp import Client
from fastmcp.utilities.skills import download_skill
async def main():
    # FastMCP default endpoint is at /mcp
    async with Client("http://localhost:8001/mcp") as c:
        tools = await c.list_tools()
        print("Discovered tools:", [t.name for t in tools])

        calc_res = await c.call_tool("calculate", {"expression": "2*(3+4)**2"})
        print("Calculate Result:", calc_res.data) # 98.0

        stats_res = await c.call_tool("word_stats", {"text": "Deep Agents protocol testing"})
        print("Word Stats Result:", stats_res.data)
        
        async with Client("http://localhost:8001/mcp") as c:
            print([str(r.uri) for r in await c.list_resources()])
            content = await c.read_resource("skill://research-brief/SKILL.md")
            print(content[0].text[:200])
            # pull a whole skill folder down, like another agent would:
            path = await download_skill(c, "research-brief", "/tmp/pulled-skills")
            print("downloaded to", path)

asyncio.run(main())




