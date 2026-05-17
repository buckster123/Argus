"""Hermes plugin wrapper for Argus MCP tools."""

from .api import router  # noqa: F401


def register(ctx):
    """Register Argus tools with Hermes gateway."""
    ctx.register_tool(
        name="argus_webcam_capture",
        toolset="argus",
        schema={
            "type": "object",
            "properties": {},
        },
        handler=lambda args, **kw: _proxy_mcp("argus_webcam_capture", args),
        emoji="📹",
    )
    ctx.register_tool(
        name="argus_screen_capture",
        toolset="argus",
        schema={
            "type": "object",
            "properties": {},
        },
        handler=lambda args, **kw: _proxy_mcp("argus_screen_capture", args),
        emoji="🖥️",
    )
    ctx.register_tool(
        name="argus_system_read",
        toolset="argus",
        schema={
            "type": "object",
            "properties": {},
        },
        handler=lambda args, **kw: _proxy_mcp("argus_system_read", args),
        emoji="🧠",
    )


def _proxy_mcp(tool_name: str, args: dict) -> str:
    """Proxy to the local Argus MCP server."""
    import json
    import subprocess

    try:
        result = subprocess.run(
            ["argus-mcp"],
            input=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": args,
                },
            }),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout
    except FileNotFoundError:
        return json.dumps({
            "error": "argus-mcp not found. Install argus-senses and ensure it's on PATH."
        })
    except Exception as e:
        return json.dumps({"error": str(e)})
