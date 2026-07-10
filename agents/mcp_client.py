import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from agents.config import ROOT_DIR, get_settings


class MCPToolError(RuntimeError):
    """Raised when an MCP tool cannot be reached or returns unusable data."""


def _default_server_command(service: str) -> tuple[str, list[str]]:
    script = ROOT_DIR / "mcp_servers" / f"{service}_server.py"
    return sys.executable, [str(script)]


def _configured_command(raw_command: Optional[str], service: str) -> tuple[str, list[str]]:
    if not raw_command:
        return _default_server_command(service)

    parts = shlex.split(raw_command, posix=os.name != "nt")
    if not parts:
        return _default_server_command(service)
    return parts[0], parts[1:]


def _decode_mcp_content(result: Any) -> Dict[str, Any]:
    content = getattr(result, "content", None)
    if not content:
        return {}

    first = content[0]
    text = getattr(first, "text", None)
    if text is None:
        return {"raw": str(first)}

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


async def call_mcp_tool(service: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Call a TripWeaver MCP tool through stdio transport.

    The agent graph depends only on this bridge. The hotel and flight service
    implementation can be swapped through environment commands without changing
    the graph nodes.
    """
    settings = get_settings()
    raw_command = settings.hotel_mcp_command if service == "hotel" else settings.flight_mcp_command
    command, args = _configured_command(raw_command, service)

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except Exception as exc:
        raise MCPToolError("The MCP Python package is not installed or could not be imported.") from exc

    try:
        env = dict(os.environ)
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(ROOT_DIR) if not existing_pythonpath else f"{ROOT_DIR}{os.pathsep}{existing_pythonpath}"
        server_params = StdioServerParameters(command=command, args=args, env=env)
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return _decode_mcp_content(result)
    except Exception as exc:
        raise MCPToolError(f"{service.title()} MCP service failed while calling {tool_name}.") from exc


async def safe_call_mcp_tool(service: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        data = await call_mcp_tool(service, tool_name, arguments)
        return {"ok": True, "data": data, "error": None}
    except MCPToolError as exc:
        return {"ok": False, "data": {}, "error": str(exc)}
