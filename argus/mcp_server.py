"""Argus MCP server — stdio transport, dynamic tools per sensor."""

import asyncio
import base64
import json
import sys
from typing import Any, Dict, List, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, ImageContent, EmbeddedResource, Tool

from argus.plugin_registry import PluginRegistry
from argus.senses.base import SenseData


app = Server("argus")
_registry: PluginRegistry | None = None


async def get_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        await _registry.discover()
    return _registry


@app.list_tools()
async def list_tools() -> List[Tool]:
    reg = await get_registry()
    tools: List[Tool] = []
    for plugin in reg.all_plugins().values():
        for t in plugin.mcp_tools():
            tools.append(
                Tool(
                    name=t["name"],
                    description=t["description"],
                    inputSchema=t.get("inputSchema", {"type": "object", "properties": {}}),
                )
            )
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: dict | None) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    reg = await get_registry()
    arguments = arguments or {}

    # Route to the plugin that owns this tool
    for plugin in reg.all_plugins().values():
        tool_names = [t["name"] for t in plugin.mcp_tools()]
        if name in tool_names:
            result: SenseData = await plugin.mcp_call(name, arguments)
            return _sense_to_mcp(result)

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


def _sense_to_mcp(data: SenseData) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    contents: List[TextContent | ImageContent | EmbeddedResource] = []

    if data.error:
        contents.append(TextContent(type="text", text=f"Sensor error: {data.error}"))
        return contents

    if data.text:
        contents.append(TextContent(type="text", text=data.text))

    if data.image:
        b64 = base64.b64encode(data.image).decode("utf-8")
        contents.append(ImageContent(type="image", data=b64, mimeType="image/jpeg"))

    if data.audio:
        # MCP spec doesn't have native audio yet; embed as base64 text note + resource link
        b64 = base64.b64encode(data.audio).decode("utf-8")
        contents.append(
            TextContent(
                type="text",
                text=f"Audio captured ({len(data.audio)} bytes, WAV). Base64:\n{b64}",
            )
        )

    if data.data:
        contents.append(TextContent(type="text", text=json.dumps(data.data, indent=2, default=str)))

    return contents


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
