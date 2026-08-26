import os
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8080/")


async def _call_get_pod_status(namespace: str) -> str:
    async with streamable_http_client(MCP_SERVER_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("get_pod_status", arguments={"namespace": namespace})
            return "\n".join(block.text for block in result.content if hasattr(block, "text"))


def get_pod_status(namespace: str = "default") -> str:
    return asyncio.run(_call_get_pod_status(namespace))
