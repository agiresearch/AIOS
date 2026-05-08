import asyncio
import os
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class MCPServerSpec:
    id: str
    transport: str  # "stdio" | "streamable_http"
    command: Optional[str] = None
    args: Optional[list[str]] = None
    env: Optional[dict[str, str]] = None
    cwd: Optional[str] = None
    url: Optional[str] = None


class MCPClientManager:
    """
    Lightweight MCP client registry.

    Exposes configured external MCP servers as tools addressable via:
      mcp/<server_id>/<tool_name>
    """

    def __init__(self, config):
        self._config = config
        self._specs: dict[str, MCPServerSpec] = {}
        self._load_specs()

    def _load_specs(self) -> None:
        self._specs = {}
        for raw in self._config.get_mcp_clients_config():
            if not isinstance(raw, dict):
                continue
            server_id = raw.get("id")
            if not server_id or not isinstance(server_id, str):
                continue
            transport = raw.get("transport", "stdio")
            spec = MCPServerSpec(
                id=server_id,
                transport=transport,
                command=raw.get("command"),
                args=raw.get("args") or None,
                env=raw.get("env") or None,
                cwd=raw.get("cwd") or None,
                url=raw.get("url") or None,
            )
            self._specs[server_id] = spec

    def refresh(self) -> None:
        self._load_specs()

    def list_server_ids(self) -> list[str]:
        return sorted(self._specs.keys())

    def get_server_spec(self, server_id: str) -> MCPServerSpec:
        if server_id not in self._specs:
            raise KeyError(f"Unknown MCP server_id '{server_id}'. Configured: {self.list_server_ids()}")
        return self._specs[server_id]

    async def _call_tool_async(self, server_id: str, tool_name: str, arguments: dict[str, Any]) -> Any:
        # Import lazily so AIOS can still run without MCP dependencies installed until needed.
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        from mcp.client.streamable_http import streamable_http_client
        from mcp import types

        spec = self.get_server_spec(server_id)

        if spec.transport == "streamable_http":
            if not spec.url:
                raise ValueError(f"MCP server '{server_id}' transport streamable_http requires 'url'")
            async with streamable_http_client(spec.url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments=arguments or {})
                    return self._normalize_call_result(result, types)

        # Default: stdio
        if not spec.command:
            raise ValueError(f"MCP server '{server_id}' transport stdio requires 'command'")

        env = dict(os.environ)
        if spec.env:
            env.update({k: str(v) for k, v in spec.env.items()})

        server_params = StdioServerParameters(
            command=spec.command,
            args=spec.args or [],
            env=env,
            cwd=spec.cwd,
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments or {})
                return self._normalize_call_result(result, types)

    def call_tool(self, server_id: str, tool_name: str, arguments: dict[str, Any]) -> Any:
        """
        Synchronous wrapper used by the current ToolManager pipeline.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Avoid nested event loops; run in a new task and wait.
            return asyncio.run_coroutine_threadsafe(
                self._call_tool_async(server_id, tool_name, arguments),
                loop,
            ).result()

        return asyncio.run(self._call_tool_async(server_id, tool_name, arguments))

    @staticmethod
    def _normalize_call_result(result, types_module) -> Any:
        # Prefer structuredContent if present.
        if getattr(result, "structuredContent", None) is not None:
            return result.structuredContent

        # Otherwise join text blocks.
        texts: list[str] = []
        for c in getattr(result, "content", []) or []:
            if isinstance(c, types_module.TextContent):
                texts.append(c.text)
        if texts:
            return "\n".join(texts)
        return str(result)


class MCPTool:
    """
    Tool wrapper compatible with the existing ToolManager interface (expects .run(params=...)).
    """

    def __init__(self, mcp_manager: MCPClientManager, server_id: str, tool_name: str):
        self._mcp = mcp_manager
        self._server_id = server_id
        self._tool_name = tool_name

    def run(self, params: dict[str, Any]) -> Any:
        return self._mcp.call_tool(self._server_id, self._tool_name, params or {})

